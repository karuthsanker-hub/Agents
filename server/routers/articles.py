"""
Articles Router
===============
Endpoints for debate article management.

SECURITY:
- Write operations require authentication
- Read operations are public for now (can be changed)
- Expensive operations (GPT analysis) require auth + rate limit

Author: Shiv Sanker
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.debate.article_manager import ArticleManager
from app.debate.article_analyzer import ArticleAnalyzer
from app.debate.seed_articles import get_seed_articles
from app.core.logging_config import api_logger as logger
from app.core.security import get_current_user, require_auth_and_rate_limit, get_current_user_optional

router = APIRouter(prefix="/articles", tags=["Articles"])


# ==================== Singleton Instances ====================

_article_manager: Optional[ArticleManager] = None
_article_analyzer: Optional[ArticleAnalyzer] = None


def get_article_manager() -> ArticleManager:
    global _article_manager
    if _article_manager is None:
        logger.info("Initializing ArticleManager")
        _article_manager = ArticleManager()
    return _article_manager


def get_article_analyzer() -> ArticleAnalyzer:
    global _article_analyzer
    if _article_analyzer is None:
        logger.info("Initializing ArticleAnalyzer")
        _article_analyzer = ArticleAnalyzer()
    return _article_analyzer


# ==================== Models ====================

class ArticleAddRequest(BaseModel):
    url: str


class ArticleSearchRequest(BaseModel):
    query: str
    n_results: int = 10


class ArticleUpdateRequest(BaseModel):
    side: Optional[str] = None
    topic_areas: Optional[List[str]] = None
    relevance_score: Optional[int] = None


# ==================== Endpoints ====================

@router.post("/add")
async def add_article(
    request: ArticleAddRequest,
    user: dict = Depends(require_auth_and_rate_limit)
):
    """
    Add and analyze a new article from URL.
    
    REQUIRES AUTHENTICATION (uses OpenAI API for analysis).
    
    The article will be fetched, analyzed by GPT, and stored in the database.
    Paywalled articles will be skipped.
    """
    logger.info(f"Adding article by {user['email']}: {request.url}")
    
    manager = get_article_manager()
    analyzer = get_article_analyzer()
    
    # Check if already exists
    existing = manager.get_article_by_url(request.url)
    if existing:
        logger.info(f"Article already exists: id={existing['id']}")
        return {
            "success": True,
            "message": "Article already exists",
            "article_id": existing['id'],
            "article": existing
        }
    
    # Fetch and analyze
    try:
        logger.info(f"Fetching and analyzing article...")
        analysis = await analyzer.analyze_url(request.url)
        
        if analysis.get('is_paywalled'):
            logger.warning(f"Article is paywalled: {request.url}")
            return {
                "success": False,
                "error": "Article appears to be paywalled or inaccessible",
                "url": request.url
            }
        
        if analysis.get('error'):
            logger.error(f"Analysis error: {analysis['error']}")
            return {
                "success": False,
                "error": analysis['error'],
                "url": request.url
            }
        
        # Store in database
        article_id = manager.add_article(analysis)
        logger.info(f"Article added successfully: id={article_id}")
        
        return {
            "success": True,
            "message": "Article added and analyzed successfully",
            "article_id": article_id,
            "analysis": {
                "title": analysis.get('title'),
                "author": analysis.get('author_name'),
                "year": analysis.get('publication_year'),
                "side": analysis.get('side'),
                "side_confidence": analysis.get('side_confidence'),
                "summary": analysis.get('summary'),
                "key_claims": analysis.get('key_claims'),
                "topic_areas": analysis.get('topic_areas'),
                "relevance_score": analysis.get('relevance_score'),
                "best_use": analysis.get('best_use')
            }
        }
        
    except Exception as e:
        logger.error(f"Error adding article: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": request.url
        }


@router.get("")
async def list_articles(
    side: Optional[str] = None,
    source_type: Optional[str] = None,
    topic_area: Optional[str] = None,
    processed_only: bool = False,
    limit: int = 50,
    offset: int = 0
):
    """
    List articles with optional filters.
    
    - **side**: aff, neg, both, neutral
    - **source_type**: news, think_tank, academic, government
    - **topic_area**: climate, security, economy, shipping, energy, etc.
    - **processed_only**: Only show fully analyzed articles
    """
    logger.info(f"Listing articles: side={side}, source_type={source_type}, topic={topic_area}, limit={limit}, offset={offset}")
    
    manager = get_article_manager()
    result = manager.list_articles(
        side=side,
        source_type=source_type,
        topic_area=topic_area,
        processed_only=processed_only,
        limit=limit,
        offset=offset
    )
    
    logger.info(f"Found {len(result['articles'])} articles (total: {result['total']})")
    return result


@router.get("/check-url")
async def check_url_exists(url: str):
    """
    Check if a URL already exists in the article library.
    
    Used to prevent duplicates before adding.
    """
    manager = get_article_manager()
    existing = manager.get_article_by_url(url)
    
    if existing:
        return {
            "exists": True,
            "article_id": existing.get("id"),
            "title": existing.get("title"),
            "message": "Article already in library"
        }
    
    return {
        "exists": False,
        "message": "URL not found in library"
    }


@router.get("/stats")
async def get_article_stats():
    """Get article library statistics."""
    logger.info("Fetching article stats")
    
    manager = get_article_manager()
    stats = manager.get_stats()
    
    return stats


@router.get("/{article_id}")
async def get_article(article_id: int):
    """Get a single article by ID with full details."""
    logger.info(f"Fetching article: id={article_id}")
    
    manager = get_article_manager()
    article = manager.get_article(article_id)
    
    if not article:
        logger.warning(f"Article not found: id={article_id}")
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


@router.post("/search")
async def search_articles(
    request: ArticleSearchRequest,
    user: dict = Depends(get_current_user)
):
    """
    Semantic search for articles.
    
    REQUIRES AUTHENTICATION.
    
    Search by meaning, not just keywords.
    Example: "Russia military threat" finds articles about Arctic security.
    """
    logger.info(f"Searching articles: query={request.query[:50]}...")
    
    manager = get_article_manager()
    results = manager.search_articles(request.query, request.n_results)
    
    logger.info(f"Search found {len(results)} results")
    return {"results": results, "count": len(results)}


@router.put("/{article_id}")
async def update_article(article_id: int, request: ArticleUpdateRequest):
    """Update article classification."""
    logger.info(f"Updating article: id={article_id}")
    
    manager = get_article_manager()
    
    updates = {}
    if request.side:
        updates['side'] = request.side
    if request.topic_areas:
        updates['topic_areas'] = request.topic_areas
    if request.relevance_score:
        updates['relevance_score'] = request.relevance_score
    
    if not updates:
        return {"success": False, "error": "No updates provided"}
    
    success = manager.update_article(article_id, updates)
    
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")
    
    logger.info(f"Article updated: id={article_id}")
    return {"success": True, "message": "Article updated"}


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    user: dict = Depends(get_current_user)
):
    """
    Delete an article from the library.
    
    REQUIRES AUTHENTICATION.
    """
    logger.info(f"Deleting article by {user['email']}: id={article_id}")
    
    manager = get_article_manager()
    deleted = manager.delete_article(article_id)
    
    if not deleted:
        logger.warning(f"Article not found for deletion: id={article_id}")
        raise HTTPException(status_code=404, detail="Article not found")
    
    logger.info(f"Article deleted: id={article_id}")
    return {"success": True, "message": "Article deleted"}


@router.post("/{article_id}/analyze")
async def analyze_article(
    article_id: int,
    user: dict = Depends(require_auth_and_rate_limit)
):
    """
    Analyze or re-analyze an article using GPT.
    
    REQUIRES AUTHENTICATION (uses OpenAI API).
    
    Useful for articles added via seed that haven't been fully analyzed.
    """
    logger.info(f"Analyzing article: id={article_id}")
    
    manager = get_article_manager()
    analyzer = get_article_analyzer()
    
    article = manager.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Fetch and analyze
    logger.info(f"Fetching URL: {article['url']}")
    analysis = await analyzer.analyze_url(article['url'])
    
    if analysis.get('error'):
        logger.error(f"Analysis error: {analysis['error']}")
        return {
            "success": False,
            "error": analysis['error'],
            "article_id": article_id
        }
    
    # Update article with analysis
    manager.update_article(article_id, {
        'title': analysis.get('title'),
        'summary': analysis.get('summary'),
        'key_claims': analysis.get('key_claims'),
        'side': analysis.get('side'),
        'side_confidence': analysis.get('side_confidence'),
        'topic_areas': analysis.get('topic_areas'),
        'supports_arguments': analysis.get('supports_arguments'),
        'against_arguments': analysis.get('against_arguments'),
        'relevance_score': analysis.get('relevance_score'),
        'is_processed': True
    })
    
    logger.info(f"Article analyzed successfully: id={article_id}, side={analysis.get('side')}")
    return {
        "success": True,
        "message": "Article analyzed successfully",
        "article_id": article_id,
        "analysis": analysis
    }


@router.post("/{article_id}/fetch")
async def fetch_article_content(
    article_id: int,
    user: dict = Depends(get_current_user)
):
    """
    Fetch the actual content of an article from its URL.
    
    REQUIRES AUTHENTICATION.
    
    Returns raw text content for card cutting. Does not analyze.
    Useful for cutting cards from articles that haven't been analyzed yet.
    """
    manager = get_article_manager()
    article = manager.get_article(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    analyzer = get_article_analyzer()
    
    logger.info(f"Fetching content from: {article['url']}")
    
    try:
        fetch_result = await analyzer.fetch_article(article['url'])
        
        if fetch_result.get('error'):
            return {
                "success": False,
                "error": fetch_result['error'],
                "article_id": article_id
            }
        
        if fetch_result.get('is_paywalled'):
            return {
                "success": False,
                "error": "Article appears to be paywalled",
                "article_id": article_id,
                "partial_content": fetch_result.get('text', '')[:500]
            }
        
        return {
            "success": True,
            "article_id": article_id,
            "title": fetch_result.get('title') or article.get('title'),
            "content": fetch_result.get('text', ''),
            "is_pdf": fetch_result.get('is_pdf', False),
            "page_count": fetch_result.get('page_count'),
            "char_count": len(fetch_result.get('text', ''))
        }
        
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }


@router.post("/seed")
async def seed_articles(user: dict = Depends(get_current_user)):
    """
    Seed the database with 40 starter Arctic articles.
    
    REQUIRES AUTHENTICATION.
    
    Articles are added with basic metadata. Use /articles/{id}/analyze 
    to get full GPT analysis for individual articles.
    """
    logger.info("Seeding article database")
    
    manager = get_article_manager()
    seed_articles = get_seed_articles()
    
    added = 0
    skipped = 0
    
    for article in seed_articles:
        existing = manager.get_article_by_url(article['url'])
        if existing:
            skipped += 1
            continue
        
        manager.add_article({
            'url': article['url'],
            'title': article.get('title'),
            'source_name': article.get('source_name'),
            'source_type': article.get('source_type'),
            'author_name': article.get('author_name'),  # Include author
            'publication_year': article.get('publication_year'),  # Include year
            'topic_areas': article.get('topic_areas', []),
            'side': article.get('expected_side'),
            'is_processed': False,
            'relevance_score': 7
        })
        added += 1
    
    logger.info(f"Seed complete: added={added}, skipped={skipped}")
    return {
        "success": True,
        "message": f"Added {added} articles, skipped {skipped} existing",
        "total_seed_articles": len(seed_articles)
    }


# ==================== Card Formatting Endpoints ====================

from app.debate.card_formatter import get_card_formatter

class FormatCardRequest(BaseModel):
    evidence_text: str
    author: str
    year: str
    title: str
    source: str
    url: Optional[str] = None
    qualifications: Optional[str] = None
    argument_context: Optional[str] = None
    generate_tag: bool = True
    highlight: bool = True


class ExtractCardsRequest(BaseModel):
    document_text: str
    topic_context: str = "Arctic policy debate"
    side: str = "aff"
    max_cards: int = 5


@router.post("/cards/format")
async def format_card(
    request: FormatCardRequest,
    user: dict = Depends(require_auth_and_rate_limit)
):
    """
    Format evidence into a proper debate card.
    
    REQUIRES AUTHENTICATION (uses OpenAI API).
    
    Takes raw evidence text and citation info, returns formatted card with:
    - AI-generated tag (one-line claim)
    - Properly formatted citation
    - Highlighted/underlined text showing key phrases
    """
    logger.info(f"Formatting card: {request.author} {request.year}")
    
    try:
        formatter = get_card_formatter()
        result = formatter.format_card(
            evidence_text=request.evidence_text,
            author=request.author,
            year=request.year,
            title=request.title,
            source=request.source,
            url=request.url,
            qualifications=request.qualifications,
            argument_context=request.argument_context,
            generate_tag=request.generate_tag,
            highlight=request.highlight
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        logger.error(f"Card formatting error: {e}")
        return {"success": False, "error": str(e)}


@router.post("/cards/extract")
async def extract_cards(
    request: ExtractCardsRequest,
    user: dict = Depends(require_auth_and_rate_limit)
):
    """
    Extract debate cards from a longer document.
    
    REQUIRES AUTHENTICATION (uses OpenAI API).
    
    Uses AI to identify the best quotable sections and suggest tags.
    Returns cards with passages that need citations added.
    """
    logger.info(f"Extracting cards from document ({len(request.document_text)} chars)")
    
    try:
        formatter = get_card_formatter()
        cards = formatter.extract_cards_from_document(
            document_text=request.document_text,
            topic_context=request.topic_context,
            side=request.side,
            max_cards=request.max_cards
        )
        
        return {
            "success": True,
            "cards": cards,
            "count": len(cards)
        }
    except Exception as e:
        logger.error(f"Card extraction error: {e}")
        return {"success": False, "error": str(e), "cards": []}

