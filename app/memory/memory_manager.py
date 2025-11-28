"""
Memory Manager
==============
Unified memory system using PostgreSQL, Redis, and ChromaDB.
Optimizes token usage through intelligent caching and semantic search.

Author: Shiv Sanker
Created: 2024
License: MIT

Architecture:
- PostgreSQL: Conversation logs, structured data, persistent storage
- Redis: Fast L1 cache for recent queries (TTL-based)
- ChromaDB: Semantic search over past conversations (vector similarity)

Cache Strategy:
1. First check Redis for exact match (fastest)
2. If miss, check ChromaDB for semantic similarity (avoids LLM call if similar answer exists)
3. Only call OpenAI if no relevant cached response found
"""

import json
import hashlib
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import chromadb

from app.core.config import get_settings
from app.core.logging_config import get_logger, verbose_db

logger = get_logger("memory")


class MemoryManager:
    """
    Manages agent memory across multiple storage systems.
    
    Features:
    - PostgreSQL: Conversation logs, structured data, analytics
    - Redis: Fast cache for recent queries with TTL
    - ChromaDB: Semantic search over past conversations
    
    Optimization Strategies:
    - Tiered caching (Redis → ChromaDB → OpenAI)
    - Semantic deduplication to reduce API calls
    - Batch operations where possible
    
    Example:
        manager = MemoryManager()
        
        # Check cache first to save tokens
        cached = manager.get_cached_response("What is the Arctic?")
        if cached:
            return cached  # No OpenAI call needed!
        
        # Check semantic memory for similar questions
        similar = manager.search_memory("What is the Arctic?")
        if similar and similar[0]['distance'] < 0.3:
            return similar[0]['content']  # Close enough match!
    """
    
    # Semantic similarity threshold for cache hits
    SEMANTIC_CACHE_THRESHOLD = 0.35
    
    def __init__(self):
        """Initialize all storage backends."""
        logger.info("Initializing MemoryManager...")
        start_time = time.time()
        
        self.settings = get_settings()
        self._init_postgres()
        self._init_redis()
        self._init_chromadb()
        
        init_time = (time.time() - start_time) * 1000
        logger.info(f"MemoryManager initialized ({init_time:.1f}ms)")
    
    # ==================== PostgreSQL ====================
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection and tables."""
        self.pg_conn = psycopg2.connect(self.settings.database_url)
        self.pg_conn.autocommit = True
        
        with self.pg_conn.cursor() as cur:
            # Create conversations table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(64),
                    role VARCHAR(20),
                    content TEXT,
                    tokens_used INTEGER DEFAULT 0,
                    response_time_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for faster session lookups
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session 
                ON conversations(session_id);
            """)
            
            # Create stats table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS agent_stats (
                    id SERIAL PRIMARY KEY,
                    date DATE DEFAULT CURRENT_DATE,
                    total_queries INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cache_hits INTEGER DEFAULT 0,
                    avg_response_ms INTEGER DEFAULT 0,
                    UNIQUE(date)
                );
            """)
    
    def log_conversation(
        self, 
        session_id: str, 
        role: str, 
        content: str,
        tokens: int = 0,
        response_time_ms: int = 0
    ) -> int:
        """Log a conversation entry to PostgreSQL."""
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO conversations (session_id, role, content, tokens_used, response_time_ms)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """, (session_id, role, content, tokens, response_time_ms))
            return cur.fetchone()[0]
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history for a session."""
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT role, content, created_at 
                FROM conversations 
                WHERE session_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s;
            """, (session_id, limit))
            return list(reversed(cur.fetchall()))
    
    def update_stats(self, tokens: int = 0, cache_hit: bool = False, response_ms: int = 0):
        """Update daily statistics."""
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO agent_stats (date, total_queries, total_tokens, cache_hits, avg_response_ms)
                VALUES (CURRENT_DATE, 1, %s, %s, %s)
                ON CONFLICT (date) DO UPDATE SET
                    total_queries = agent_stats.total_queries + 1,
                    total_tokens = agent_stats.total_tokens + EXCLUDED.total_tokens,
                    cache_hits = agent_stats.cache_hits + EXCLUDED.cache_hits,
                    avg_response_ms = (agent_stats.avg_response_ms + EXCLUDED.avg_response_ms) / 2;
            """, (tokens, 1 if cache_hit else 0, response_ms))
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM agent_stats 
                WHERE date = CURRENT_DATE;
            """)
            today = cur.fetchone()
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_conversations,
                    COUNT(DISTINCT session_id) as unique_sessions
                FROM conversations;
            """)
            totals = cur.fetchone()
            
            return {
                "today": dict(today) if today else {},
                "totals": dict(totals) if totals else {}
            }
    
    # ==================== Redis Cache ====================
    
    def _init_redis(self):
        """Initialize Redis connection."""
        self.redis = redis.from_url(self.settings.redis_url)
    
    def _cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return f"agent:cache:{hashlib.md5(query.lower().strip().encode()).hexdigest()}"
    
    def get_cached_response(self, query: str) -> Optional[str]:
        """Check if response is cached in Redis."""
        key = self._cache_key(query)
        cached = self.redis.get(key)
        if cached:
            return cached.decode('utf-8')
        return None
    
    def cache_response(self, query: str, response: str, ttl: int = None):
        """Cache response in Redis."""
        key = self._cache_key(query)
        ttl = ttl or self.settings.cache_ttl
        self.redis.setex(key, ttl, response)
    
    def get_rate_limit(self, session_id: str) -> int:
        """Get remaining rate limit for session."""
        key = f"agent:ratelimit:{session_id}"
        count = self.redis.get(key)
        if count is None:
            return 100  # Default limit
        return max(0, 100 - int(count))
    
    def increment_rate_limit(self, session_id: str):
        """Increment rate limit counter."""
        key = f"agent:ratelimit:{session_id}"
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)  # Reset hourly
        pipe.execute()
    
    # ==================== ChromaDB Vector Store ====================
    
    def _init_chromadb(self):
        """
        Initialize ChromaDB for semantic memory and response caching.
        
        Creates two collections:
        - agent_memory: General conversation memory for context
        - agent_responses: Cached responses for semantic deduplication
        """
        logger.debug("Initializing ChromaDB...")
        
        self.chroma = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
        
        # Collection for general conversation memory
        self.memory_collection = self.chroma.get_or_create_collection(
            name="agent_memory",
            metadata={"description": "Agent conversation memory for semantic search"}
        )
        
        # Collection for response caching (semantic deduplication)
        self.response_collection = self.chroma.get_or_create_collection(
            name="agent_responses",
            metadata={"description": "Cached responses for semantic similarity lookup"}
        )
        
        logger.debug(f"ChromaDB collections: memory={self.memory_collection.count()}, responses={self.response_collection.count()}")
    
    def store_memory(self, session_id: str, content: str, role: str = "user"):
        """Store content in vector memory for semantic search."""
        doc_id = f"{session_id}_{datetime.now().timestamp()}"
        self.memory_collection.add(
            documents=[content],
            metadatas=[{
                "session_id": session_id,
                "role": role,
                "timestamp": datetime.now().isoformat()
            }],
            ids=[doc_id]
        )
    
    def search_memory(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Search past conversations semantically using ChromaDB.
        
        Args:
            query: The search query
            n_results: Maximum number of results to return
            
        Returns:
            List of memory dicts with content, metadata, and distance scores
        """
        start_time = time.time()
        
        results = self.memory_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        memories = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                memories.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        query_time = (time.time() - start_time) * 1000
        logger.debug(f"ChromaDB search: {len(memories)} results ({query_time:.1f}ms)")
        
        return memories
    
    def get_semantic_cache(self, query: str) -> Optional[Tuple[str, float]]:
        """
        Check ChromaDB for semantically similar cached responses.
        
        This is a key optimization - if a very similar question was asked before,
        we can return the cached answer without calling OpenAI.
        
        Args:
            query: The user's query
            
        Returns:
            Tuple of (cached_response, similarity_score) if found, None otherwise
        """
        # Search for similar assistant responses
        results = self.response_collection.query(
            query_texts=[query],
            n_results=1,
            where={"role": "assistant"}
        )
        
        if results['documents'] and results['documents'][0]:
            distance = results['distances'][0][0] if results['distances'] else 1.0
            
            # Lower distance = more similar
            if distance < self.SEMANTIC_CACHE_THRESHOLD:
                response = results['documents'][0][0]
                similarity = 1 - distance
                logger.info(f"🎯 Semantic cache hit! Similarity: {similarity:.2%}")
                return (response, similarity)
        
        return None
    
    def cache_response_semantic(self, query: str, response: str, session_id: str = None):
        """
        Cache a query-response pair in ChromaDB for semantic retrieval.
        
        This allows future similar queries to retrieve this response
        without making an OpenAI API call.
        
        Args:
            query: The user's query
            response: The assistant's response
            session_id: Optional session identifier
        """
        doc_id = f"resp_{hashlib.md5(query.encode()).hexdigest()[:12]}_{int(time.time())}"
        
        # Store the response with the query as searchable content
        self.response_collection.add(
            documents=[response],
            metadatas=[{
                "query": query[:500],  # Store query for reference
                "role": "assistant",
                "session_id": session_id or "unknown",
                "timestamp": datetime.now().isoformat()
            }],
            ids=[doc_id]
        )
        logger.debug(f"Cached response semantically: {doc_id}")
    
    def get_memory_count(self) -> int:
        """Get total memories stored."""
        return self.memory_collection.count()
    
    # ==================== Cleanup ====================
    
    def close(self):
        """Close all connections."""
        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()
        if hasattr(self, 'redis'):
            self.redis.close()

