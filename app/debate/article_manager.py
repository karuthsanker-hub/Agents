"""
Article Manager
===============
Manages article storage and retrieval for debate research.
Uses PostgreSQL for structured data and ChromaDB for semantic search.
"""

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import chromadb

from app.core.config import get_settings
from app.core.logging_config import db_logger as logger


class ArticleManager:
    """
    Manages debate research articles across PostgreSQL and ChromaDB.
    
    Features:
    - Store article metadata and full text
    - Semantic search for relevant articles
    - Filter by side (aff/neg), topic area, source type
    - Track article usage and card cutting
    """
    
    def __init__(self):
        logger.info("Initializing ArticleManager")
        self.settings = get_settings()
        self._init_postgres()
        self._init_chromadb()
        logger.info("ArticleManager initialized successfully")
    
    # ==================== Database Setup ====================
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection and create tables."""
        self.pg_conn = psycopg2.connect(self.settings.database_url)
        self.pg_conn.autocommit = True
        
        with self.pg_conn.cursor() as cur:
            # Create articles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id SERIAL PRIMARY KEY,
                    
                    -- Source Info
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    source_name VARCHAR(200),
                    source_type VARCHAR(50),
                    
                    -- Author Info
                    author_name VARCHAR(200),
                    author_credentials TEXT,
                    publication_date DATE,
                    publication_year INTEGER,
                    
                    -- Content
                    full_text TEXT,
                    summary TEXT,
                    key_claims JSONB,
                    evidence_excerpt TEXT,
                    evidence_context TEXT,
                    
                    -- Debate Classification
                    side VARCHAR(20),
                    side_confidence FLOAT,
                    topic_areas TEXT[],
                    supports_arguments TEXT[],
                    against_arguments TEXT[],
                    relevance_score INTEGER,
                    
                    -- Status
                    is_processed BOOLEAN DEFAULT FALSE,
                    is_paywalled BOOLEAN DEFAULT FALSE,
                    cards_cut INTEGER DEFAULT 0,
                    times_viewed INTEGER DEFAULT 0,
                    
                    -- Metadata
                    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    last_accessed TIMESTAMP
                );
                
                -- Indexes for fast searching
                CREATE INDEX IF NOT EXISTS idx_articles_side ON articles(side);
                CREATE INDEX IF NOT EXISTS idx_articles_source_type ON articles(source_type);
                CREATE INDEX IF NOT EXISTS idx_articles_processed ON articles(is_processed);
                CREATE INDEX IF NOT EXISTS idx_articles_relevance ON articles(relevance_score DESC);
            """)
            
            cur.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS evidence_excerpt TEXT;
            """)
            cur.execute("""
                ALTER TABLE articles
                ADD COLUMN IF NOT EXISTS evidence_context TEXT;
            """)
            
            # Create debate_cards table (for later use)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS debate_cards (
                    id SERIAL PRIMARY KEY,
                    article_id INTEGER REFERENCES articles(id),
                    
                    -- Card Content
                    tag TEXT NOT NULL,
                    cite_full TEXT,
                    card_body TEXT NOT NULL,
                    card_highlighted TEXT,
                    
                    -- Classification
                    side VARCHAR(10),
                    argument_type VARCHAR(50),
                    topic_area VARCHAR(100),
                    
                    -- Metadata
                    quality_score INTEGER,
                    times_used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def _init_chromadb(self):
        """Initialize ChromaDB for semantic search."""
        self.chroma = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
        self.article_collection = self.chroma.get_or_create_collection(
            name="debate_articles",
            metadata={"description": "Arctic debate topic articles for semantic search"}
        )
    
    # ==================== Article CRUD ====================
    
    def add_article(self, article_data: Dict[str, Any]) -> int:
        """
        Add a new article to the database.
        
        Args:
            article_data: Dictionary with article information
            
        Returns:
            Article ID
        """
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO articles (
                    url, title, source_name, source_type,
                    author_name, author_credentials, publication_date, publication_year,
                    full_text, summary, key_claims, evidence_excerpt, evidence_context,
                    side, side_confidence, topic_areas, supports_arguments, against_arguments,
                    relevance_score, is_processed, is_paywalled, processed_at
                ) VALUES (
                    %(url)s, %(title)s, %(source_name)s, %(source_type)s,
                    %(author_name)s, %(author_credentials)s, %(publication_date)s, %(publication_year)s,
                    %(full_text)s, %(summary)s, %(key_claims)s, %(evidence_excerpt)s, %(evidence_context)s,
                    %(side)s, %(side_confidence)s, %(topic_areas)s, %(supports_arguments)s, %(against_arguments)s,
                    %(relevance_score)s, %(is_processed)s, %(is_paywalled)s, %(processed_at)s
                )
                ON CONFLICT (url) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    key_claims = EXCLUDED.key_claims,
                    evidence_excerpt = EXCLUDED.evidence_excerpt,
                    evidence_context = EXCLUDED.evidence_context,
                    side = EXCLUDED.side,
                    is_processed = EXCLUDED.is_processed,
                    processed_at = EXCLUDED.processed_at
                RETURNING id;
            """, {
                'url': article_data.get('url'),
                'title': article_data.get('title'),
                'source_name': article_data.get('source_name'),
                'source_type': article_data.get('source_type'),
                'author_name': article_data.get('author_name'),
                'author_credentials': article_data.get('author_credentials'),
                'publication_date': article_data.get('publication_date'),
                'publication_year': article_data.get('publication_year'),
                'full_text': article_data.get('full_text'),
                'summary': article_data.get('summary'),
                'key_claims': Json(article_data.get('key_claims', [])),
                'evidence_excerpt': article_data.get('evidence_excerpt'),
                'evidence_context': article_data.get('evidence_context'),
                'side': article_data.get('side'),
                'side_confidence': article_data.get('side_confidence'),
                'topic_areas': article_data.get('topic_areas', []),
                'supports_arguments': article_data.get('supports_arguments', []),
                'against_arguments': article_data.get('against_arguments', []),
                'relevance_score': article_data.get('relevance_score', 5),
                'is_processed': article_data.get('is_processed', False),
                'is_paywalled': article_data.get('is_paywalled', False),
                'processed_at': datetime.now() if article_data.get('is_processed') else None
            })
            article_id = cur.fetchone()[0]
        
        # Also store in ChromaDB for semantic search
        if article_data.get('summary') or article_data.get('full_text'):
            search_text = f"{article_data.get('title', '')} {article_data.get('summary', '')} {' '.join(article_data.get('key_claims', []))}"
            self.article_collection.upsert(
                ids=[str(article_id)],
                documents=[search_text],
                metadatas=[{
                    "article_id": article_id,
                    "title": article_data.get('title', ''),
                    "side": article_data.get('side', 'neutral'),
                    "source_type": article_data.get('source_type', ''),
                    "relevance_score": article_data.get('relevance_score', 5)
                }]
            )
        
        return article_id
    
    def get_article(self, article_id: int) -> Optional[Dict]:
        """Get a single article by ID."""
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                UPDATE articles SET 
                    times_viewed = times_viewed + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *;
            """, (article_id,))
            result = cur.fetchone()
            return dict(result) if result else None
    
    def get_article_by_url(self, url: str) -> Optional[Dict]:
        """Get article by URL."""
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM articles WHERE url = %s;", (url,))
            result = cur.fetchone()
            return dict(result) if result else None
    
    def list_articles(
        self,
        side: Optional[str] = None,
        source_type: Optional[str] = None,
        topic_area: Optional[str] = None,
        processed_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        List articles with optional filters.
        
        Args:
            side: Filter by 'aff', 'neg', 'both', or 'neutral'
            source_type: Filter by 'news', 'think_tank', 'academic', 'government'
            topic_area: Filter by topic like 'climate', 'security'
            processed_only: Only show analyzed articles
            limit: Maximum results
            offset: Pagination offset
        """
        conditions = []
        params = []
        
        if side:
            conditions.append("side = %s")
            params.append(side)
        
        if source_type:
            conditions.append("source_type = %s")
            params.append(source_type)
        
        if topic_area:
            conditions.append("%s = ANY(topic_areas)")
            params.append(topic_area)
        
        if processed_only:
            conditions.append("is_processed = TRUE")
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get total count first (for pagination)
            count_params = params.copy()
            cur.execute(f"""
                SELECT COUNT(*) as total FROM articles {where_clause}
            """, count_params)
            total_count = cur.fetchone()['total']
            
            # Get paginated results
            params.extend([limit, offset])
            cur.execute(f"""
                SELECT id, url, title, source_name, source_type, author_name,
                       publication_year, summary, side, side_confidence,
                       topic_areas, relevance_score, is_processed, cards_cut,
                       discovered_at, evidence_excerpt, evidence_context
                FROM articles
                {where_clause}
                ORDER BY relevance_score DESC NULLS LAST, discovered_at DESC
                LIMIT %s OFFSET %s;
            """, params)
            articles = [dict(row) for row in cur.fetchall()]
            
            return {
                "articles": articles,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(articles)) < total_count
            }
    
    def search_articles(self, query: str, n_results: int = 10) -> List[Dict]:
        """
        Semantic search for articles.
        
        Args:
            query: Search query (e.g., "Russia military threat Arctic")
            n_results: Number of results to return
        """
        results = self.article_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        articles = []
        if results['ids'] and results['ids'][0]:
            for i, article_id in enumerate(results['ids'][0]):
                article = self.get_article(int(article_id))
                if article:
                    article['search_distance'] = results['distances'][0][i] if results['distances'] else None
                    articles.append(article)
        
        return articles
    
    def update_article(self, article_id: int, updates: Dict[str, Any]) -> bool:
        """Update article fields."""
        allowed_fields = [
            'title', 'summary', 'key_claims', 'side', 'side_confidence',
            'topic_areas', 'supports_arguments', 'against_arguments',
            'relevance_score', 'is_processed', 'full_text'
        ]
        
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                if field == 'key_claims':
                    set_clauses.append(f"{field} = %s")
                    params.append(Json(value))
                else:
                    set_clauses.append(f"{field} = %s")
                    params.append(value)
        
        if not set_clauses:
            return False
        
        params.append(article_id)
        
        with self.pg_conn.cursor() as cur:
            cur.execute(f"""
                UPDATE articles 
                SET {', '.join(set_clauses)}
                WHERE id = %s;
            """, params)
            return cur.rowcount > 0

    def update_evidence_fields(
        self,
        article_id: int,
        *,
        full_text: Optional[str] = None,
        evidence_excerpt: Optional[str] = None,
        evidence_context: Optional[str] = None
    ) -> bool:
        """Update evidence excerpt/context (and optionally full text)."""
        set_clauses = []
        params = []
        
        if full_text is not None:
            set_clauses.append("full_text = %s")
            params.append(full_text)
        if evidence_excerpt is not None:
            set_clauses.append("evidence_excerpt = %s")
            params.append(evidence_excerpt)
        if evidence_context is not None:
            set_clauses.append("evidence_context = %s")
            params.append(evidence_context)
        
        if not set_clauses:
            return False
        
        params.append(article_id)
        with self.pg_conn.cursor() as cur:
            cur.execute(f"""
                UPDATE articles
                SET {', '.join(set_clauses)},
                    processed_at = processed_at
                WHERE id = %s;
            """, params)
            return cur.rowcount > 0
    
    def delete_article(self, article_id: int) -> bool:
        """Delete an article."""
        with self.pg_conn.cursor() as cur:
            cur.execute("DELETE FROM articles WHERE id = %s;", (article_id,))
            deleted = cur.rowcount > 0
        
        if deleted:
            try:
                self.article_collection.delete(ids=[str(article_id)])
            except:
                pass
        
        return deleted
    
    def increment_cards_cut(self, article_id: int) -> bool:
        """Increment the cards_cut counter for an article."""
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                UPDATE articles SET cards_cut = cards_cut + 1
                WHERE id = %s;
            """, (article_id,))
            return cur.rowcount > 0
    
    # ==================== Statistics ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get article library statistics."""
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_articles,
                    COUNT(*) FILTER (WHERE is_processed = TRUE) as processed_articles,
                    COUNT(*) FILTER (WHERE side = 'aff') as aff_articles,
                    COUNT(*) FILTER (WHERE side = 'neg') as neg_articles,
                    COUNT(*) FILTER (WHERE side = 'both') as both_articles,
                    COUNT(*) FILTER (WHERE source_type = 'news') as news_count,
                    COUNT(*) FILTER (WHERE source_type = 'think_tank') as think_tank_count,
                    COUNT(*) FILTER (WHERE source_type = 'academic') as academic_count,
                    COUNT(*) FILTER (WHERE source_type = 'government') as gov_count,
                    COALESCE(SUM(cards_cut), 0) as total_cards_cut,
                    COALESCE(AVG(relevance_score), 0) as avg_relevance
                FROM articles;
            """)
            stats = dict(cur.fetchone())
            
            # Get topic area counts
            cur.execute("""
                SELECT unnest(topic_areas) as topic, COUNT(*) as count
                FROM articles
                WHERE topic_areas IS NOT NULL
                GROUP BY topic
                ORDER BY count DESC;
            """)
            stats['topic_counts'] = {row['topic']: row['count'] for row in cur.fetchall()}
            
            return stats
    
    def close(self):
        """Close database connections."""
        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()

