"""
Article Analyzer
================
Uses GPT to analyze articles and extract debate-relevant information.
Classifies articles as Aff/Neg, extracts key claims, and generates summaries.
Supports HTML articles and PDF documents.

Prompts are stored in the database and can be customized via Admin panel.

Author: Shiv Sanker
"""

import json
import re
import io
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.logging_config import analyzer_logger as logger
from app.core.admin_config import get_admin_config
from app.core.prompt_manager import get_prompt_manager

# Trusted domains that are never paywalled
TRUSTED_DOMAINS = [
    'govinfo.gov', 'gov', 'congress.gov', 'gpo.gov',
    'state.gov', 'defense.gov', 'noaa.gov', 'usgs.gov',
    'nsf.gov', 'nasa.gov', 'uscg.mil', 'army.mil', 'navy.mil',
    'arctic-council.org', 'un.org', 'worldbank.org',
    'crs.gov', 'fas.org', 'gao.gov'
]


class ArticleAnalyzer:
    """
    Analyzes articles for debate research using GPT.
    
    Capabilities:
    - Fetch article content from URL
    - Extract author, date, source information
    - Generate debate-focused summary
    - Classify as Affirmative or Negative evidence
    - Extract key claims and warrants
    """
    
    # Arctic topic context for better analysis
    TOPIC_CONTEXT = """
    The 2025-2026 Policy Debate Resolution is:
    "Resolved: The United States federal government should significantly increase 
    its exploration and/or development of the Arctic."
    
    Key topic areas include:
    - Energy (oil, gas, renewables)
    - Shipping (Northern Sea Route, Northwest Passage)
    - Security (Russia, China, military presence)
    - Climate change and environmental impacts
    - Indigenous rights and sovereignty
    - Scientific research
    - Mining and rare earth minerals
    - Coast Guard and icebreaker capacity
    """
    
    ANALYSIS_PROMPT = """You are a debate coach helping an 11th grade policy debater analyze articles for the Arctic topic.

{topic_context}

Analyze this article and extract information useful for debate. Write the summary in clear, accessible language that a high school junior would use - avoid jargon, be direct, and explain WHY this matters for debate.

ARTICLE TITLE: {title}
ARTICLE SOURCE: {source}
ARTICLE TEXT:
{text}

Provide your analysis in the following JSON format:
{{
    "title": "Article title (cleaned up if needed)",
    "author_name": "Author's full name or 'Unknown'",
    "author_credentials": "Author's title, position, expertise (if mentioned)",
    "publication_year": YYYY (integer, or null if unknown),
    "source_name": "Publication name",
    "source_type": "news|think_tank|academic|government",
    
    "summary": "Write 2-3 sentences like you're explaining to a friend: What's the main point? Why does it matter for the Arctic debate? Use simple, clear language an 11th grader would naturally use.",
    
    "key_claims": [
        "First major claim - state it clearly and simply",
        "Second major claim - what's the evidence saying?",
        "Third major claim (up to 5 total)"
    ],
    
    "side": "aff|neg|both|neutral",
    "side_confidence": 0.0-1.0,
    "side_explanation": "One sentence explaining why - does it support expanding Arctic activity (aff) or argue against it (neg)?",
    
    "topic_areas": ["area1", "area2"],
    "supports_arguments": ["What specific debate arguments can you run with this? Be specific!"],
    "against_arguments": ["What opponent arguments does this help you answer?"],
    
    "relevance_score": 1-10,
    "best_use": "When would you read this card? (e.g., '1AC Advantage 2 - Indigenous Rights', 'Neg answers to security aff')"
}}

Valid topic_areas: climate, security, economy, shipping, energy, indigenous, research, environment, military, mining, diplomacy
Valid source_types: news, think_tank, academic, government

Respond ONLY with valid JSON, no other text."""

    def __init__(self):
        logger.info("Initializing ArticleAnalyzer")
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model
        self.admin_config = get_admin_config()
        self.prompt_manager = get_prompt_manager()
        logger.info(f"ArticleAnalyzer initialized with model: {self.model}")
    
    def _get_topic_context(self) -> str:
        """Get topic context from database or fallback to default."""
        db_prompt = self.prompt_manager.get_prompt("topic_context")
        return db_prompt if db_prompt else self.TOPIC_CONTEXT
    
    def _get_analysis_prompt(self) -> str:
        """Get analysis prompt from database or fallback to default."""
        db_prompt = self.prompt_manager.get_prompt("article_analysis")
        return db_prompt if db_prompt else self.ANALYSIS_PROMPT
    
    def _is_trusted_domain(self, url: str) -> bool:
        """Check if URL is from a trusted (non-paywalled) domain."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        return any(trusted in domain for trusted in TRUSTED_DOMAINS)
    
    def _is_pdf_url(self, url: str) -> bool:
        """Check if URL points to a PDF."""
        return url.lower().endswith('.pdf') or '/pdf/' in url.lower()
    
    async def _fetch_pdf(self, url: str) -> Dict[str, Any]:
        """Fetch and extract text from a PDF URL."""
        logger.info(f"Fetching PDF: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Read PDF content
                pdf_bytes = response.content
                pdf_file = io.BytesIO(pdf_bytes)
                reader = PdfReader(pdf_file)
                
                # Extract text from all pages
                text_parts = []
                for page in reader.pages[:50]:  # Limit to first 50 pages
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                full_text = '\n\n'.join(text_parts)
                full_text = self._clean_text(full_text)
                
                # Try to get title from metadata or first lines
                title = None
                if reader.metadata and reader.metadata.title:
                    title = reader.metadata.title
                if not title and text_parts:
                    # Get first non-empty line as title
                    first_lines = text_parts[0].split('\n')[:5]
                    for line in first_lines:
                        line = line.strip()
                        if len(line) > 10 and len(line) < 200:
                            title = line
                            break
                
                logger.info(f"PDF extracted: {len(full_text)} chars, {len(reader.pages)} pages")
                
                return {
                    'text': full_text[:20000],  # PDFs can be longer
                    'title': title,
                    'is_paywalled': False,  # If we got the PDF, it's not paywalled
                    'url': url,
                    'error': None,
                    'is_pdf': True,
                    'page_count': len(reader.pages)
                }
                
        except Exception as e:
            logger.error(f"PDF fetch error: {e}")
            return {'text': '', 'title': None, 'is_paywalled': False, 'url': url, 'error': f"PDF error: {str(e)}"}
    
    async def fetch_article(self, url: str) -> Dict[str, Any]:
        """
        Fetch article content from URL.
        Supports HTML pages and PDF documents.
        
        Returns:
            Dict with 'text', 'title', 'is_paywalled', 'error'
        """
        logger.info(f"Fetching article: {url}")
        
        # Check if it's a PDF
        if self._is_pdf_url(url):
            return await self._fetch_pdf(url)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        is_trusted = self._is_trusted_domain(url)
        
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Check if response is actually a PDF
                content_type = response.headers.get('content-type', '')
                if 'application/pdf' in content_type:
                    return await self._fetch_pdf(url)
                
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove unwanted elements
                for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'iframe']):
                    tag.decompose()
                
                # Try to get title
                title = None
                if soup.title:
                    title = soup.title.string
                if not title:
                    h1 = soup.find('h1')
                    if h1:
                        title = h1.get_text(strip=True)
                
                # Try to get article content
                article_text = ""
                
                # Look for article body
                article_selectors = [
                    'article', '.article-body', '.post-content', '.entry-content',
                    '.article-content', '#article-body', '.story-body', 'main'
                ]
                
                for selector in article_selectors:
                    content = soup.select_one(selector)
                    if content:
                        article_text = content.get_text(separator='\n', strip=True)
                        break
                
                # Fallback to body if no article found
                if not article_text:
                    body = soup.find('body')
                    if body:
                        article_text = body.get_text(separator='\n', strip=True)
                
                # Clean up text
                article_text = self._clean_text(article_text)
                
                # Check for paywall indicators (skip for trusted domains)
                is_paywalled = False
                if not is_trusted:
                    paywall_indicators = [
                        'subscribe to read', 'subscription required', 'sign in to read',
                        'members only', 'premium content', 'paywall', 'subscribe now to continue'
                    ]
                    is_paywalled = any(ind in article_text.lower() for ind in paywall_indicators)
                    
                    # If text is too short, might be paywalled
                    if len(article_text) < 500:
                        is_paywalled = True
                
                logger.info(f"Article fetched: {len(article_text)} chars, paywalled={is_paywalled}")
                
                return {
                    'text': article_text[:15000],
                    'title': title,
                    'is_paywalled': is_paywalled,
                    'url': url,
                    'error': None
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            return {'text': '', 'title': None, 'is_paywalled': True, 'url': url, 'error': f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return {'text': '', 'title': None, 'is_paywalled': True, 'url': url, 'error': str(e)}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize article text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common junk
        junk_patterns = [
            r'Advertisement\s*', r'ADVERTISEMENT\s*',
            r'Share this article\s*', r'Share on.*?\n',
            r'Follow us on.*?\n', r'Sign up for.*?\n',
            r'Copyright ©.*?\n', r'All rights reserved.*?\n'
        ]
        for pattern in junk_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def analyze_article(
        self, 
        text: str, 
        title: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze article text using GPT.
        
        Args:
            text: Article text content
            title: Article title (optional)
            source: Source URL or name (optional)
            
        Returns:
            Analysis dictionary with debate-relevant information
        """
        if not text or len(text) < 100:
            return {'error': 'Article text too short or empty'}
        
        # Truncate if too long
        if len(text) > 12000:
            text = text[:12000] + "\n\n[Article truncated due to length]"
        
        # Get prompts from database (customizable via Admin panel)
        topic_context = self._get_topic_context()
        analysis_prompt = self._get_analysis_prompt()
        
        prompt = analysis_prompt.format(
            topic_context=topic_context,
            title=title or "Unknown",
            source=source or "Unknown",
            text=text
        )
        
        # Check rate limits
        rate_check = self.admin_config.check_rate_limit()
        if not rate_check.get('allowed', True):
            logger.warning(f"Rate limit exceeded: {rate_check.get('reason')}")
            return {
                'error': rate_check.get('reason', 'Rate limit exceeded'),
                'rate_limit_exceeded': True
            }
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a debate research expert. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=2000,
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 1500
            
            # Track usage
            self.admin_config.track_usage(
                endpoint="article_analyze",
                tokens_used=tokens_used,
                model=self.model
            )
            
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                result_text = json_match.group()
            
            analysis = json.loads(result_text)
            analysis['tokens_used'] = tokens_used
            
            return analysis
            
        except json.JSONDecodeError as e:
            return {'error': f'Failed to parse GPT response: {e}', 'raw_response': result_text}
        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}
    
    async def analyze_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch and analyze article from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Complete analysis with fetch status
        """
        # Fetch article
        fetch_result = await self.fetch_article(url)
        
        if fetch_result.get('error'):
            return {
                'url': url,
                'is_paywalled': True,
                'error': fetch_result['error'],
                'is_processed': False
            }
        
        if fetch_result.get('is_paywalled'):
            return {
                'url': url,
                'title': fetch_result.get('title'),
                'is_paywalled': True,
                'error': 'Article appears to be paywalled or content is too short',
                'is_processed': False
            }
        
        # Analyze content
        analysis = self.analyze_article(
            text=fetch_result['text'],
            title=fetch_result.get('title'),
            source=url
        )
        
        if analysis.get('error'):
            return {
                'url': url,
                'title': fetch_result.get('title'),
                'is_paywalled': False,
                'error': analysis['error'],
                'is_processed': False
            }
        
        # Combine results
        result = {
            'url': url,
            'full_text': fetch_result['text'],
            'is_paywalled': False,
            'is_processed': True,
            **analysis
        }
        
        return result


# Synchronous wrapper for non-async contexts
def analyze_url_sync(url: str) -> Dict[str, Any]:
    """Synchronous wrapper for analyze_url."""
    import asyncio
    analyzer = ArticleAnalyzer()
    return asyncio.run(analyzer.analyze_url(url))

