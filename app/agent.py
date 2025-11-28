"""
Research Assistant Agent
========================
A smart AI agent that uses all configured services:
- OpenAI for reasoning
- PostgreSQL for logging
- Redis for caching
- ChromaDB for semantic memory
- Admin config for rate limiting
"""

import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from openai import OpenAI

from app.core.config import get_settings
from app.core.admin_config import get_admin_config
from app.memory.memory_manager import MemoryManager


class ResearchAgent:
    """
    A research assistant agent with memory and caching capabilities.
    
    Features:
    - Intelligent responses using GPT
    - Conversation logging (PostgreSQL)
    - Response caching (Redis)
    - Semantic memory search (ChromaDB)
    """
    
    SYSTEM_PROMPT = """You are a helpful research assistant with access to your memory of past conversations.

Your capabilities:
1. Answer questions accurately and helpfully
2. Remember context from the current conversation
3. Recall relevant information from past conversations when provided
4. Be concise but thorough

When given relevant memories from past conversations, use them to provide better context-aware answers.
Always be helpful, accurate, and friendly."""

    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.memory = MemoryManager()
        self.model = self.settings.openai_model
        self.admin_config = get_admin_config()
    
    def chat(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        use_cache: bool = True,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: User's message
            session_id: Session identifier (auto-generated if not provided)
            use_cache: Whether to check/use cached responses
            use_memory: Whether to search semantic memory
            
        Returns:
            Dict with response, metadata, and stats
        """
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())[:8]
        
        # Check admin rate limits first
        rate_check = self.admin_config.check_rate_limit(session_id)
        if not rate_check.get('allowed', True):
            return {
                "success": False,
                "error": rate_check.get('reason', 'Rate limit exceeded'),
                "session_id": session_id,
                "rate_limit_info": rate_check
            }
        
        # Check per-session rate limit
        remaining = self.memory.get_rate_limit(session_id)
        if remaining <= 0:
            return {
                "success": False,
                "error": "Rate limit exceeded. Please try again later.",
                "session_id": session_id
            }
        
        # ==================== CACHE LAYER 1: Redis (Exact Match) ====================
        cached_response = None
        if use_cache:
            cached_response = self.memory.get_cached_response(message)
            if cached_response:
                response_time = int((time.time() - start_time) * 1000)
                self.memory.update_stats(tokens=0, cache_hit=True, response_ms=response_time)
                return {
                    "success": True,
                    "response": cached_response,
                    "session_id": session_id,
                    "cached": True,
                    "cache_type": "redis_exact",
                    "response_time_ms": response_time,
                    "tokens_used": 0
                }
        
        # ==================== CACHE LAYER 2: ChromaDB (Semantic Match) ====================
        if use_cache:
            semantic_cache = self.memory.get_semantic_cache(message)
            if semantic_cache:
                response_text, similarity = semantic_cache
                response_time = int((time.time() - start_time) * 1000)
                self.memory.update_stats(tokens=0, cache_hit=True, response_ms=response_time)
                return {
                    "success": True,
                    "response": response_text,
                    "session_id": session_id,
                    "cached": True,
                    "cache_type": "chromadb_semantic",
                    "similarity_score": similarity,
                    "response_time_ms": response_time,
                    "tokens_used": 0
                }
        
        # ==================== Memory Context ====================
        # Search semantic memory for relevant context
        relevant_memories = []
        if use_memory:
            relevant_memories = self.memory.search_memory(message, n_results=3)
        
        # Build conversation context
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        # Add relevant memories as context
        if relevant_memories:
            memory_context = "Relevant information from past conversations:\n"
            for mem in relevant_memories:
                memory_context += f"- {mem['content']}\n"
            messages.append({
                "role": "system", 
                "content": memory_context
            })
        
        # Get recent conversation history
        history = self.memory.get_conversation_history(session_id, limit=6)
        for entry in history:
            messages.append({
                "role": entry["role"],
                "content": entry["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1000,
                temperature=self.settings.openai_temperature
            )
            
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Track usage in admin config
            self.admin_config.track_usage(
                endpoint="chat",
                tokens_used=tokens_used,
                session_id=session_id,
                model=self.model
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": f"OpenAI API error: {str(e)}",
                "session_id": session_id
            }
        
        response_time = int((time.time() - start_time) * 1000)
        
        # Log conversation to PostgreSQL
        self.memory.log_conversation(session_id, "user", message)
        self.memory.log_conversation(
            session_id, "assistant", assistant_message, 
            tokens=tokens_used, response_time_ms=response_time
        )
        
        # Store in semantic memory for context
        self.memory.store_memory(session_id, message, role="user")
        self.memory.store_memory(session_id, assistant_message, role="assistant")
        
        # Cache the response (both Redis and ChromaDB for tiered caching)
        if use_cache:
            # Redis: Exact match cache (fast, TTL-based)
            self.memory.cache_response(message, assistant_message)
            # ChromaDB: Semantic cache (for similar questions)
            self.memory.cache_response_semantic(message, assistant_message, session_id)
        
        # Update stats
        self.memory.update_stats(tokens=tokens_used, cache_hit=False, response_ms=response_time)
        
        # Increment rate limit
        self.memory.increment_rate_limit(session_id)
        
        return {
            "success": True,
            "response": assistant_message,
            "session_id": session_id,
            "cached": False,
            "response_time_ms": response_time,
            "tokens_used": tokens_used,
            "memories_used": len(relevant_memories)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            "database": self.memory.get_stats(),
            "memory_count": self.memory.get_memory_count(),
            "model": self.model
        }
    
    def search_memories(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search semantic memory."""
        return self.memory.search_memory(query, n_results)
    
    def get_history(self, session_id: str, limit: int = 20) -> List[Dict]:
        """Get conversation history for a session."""
        return self.memory.get_conversation_history(session_id, limit)
    
    def close(self):
        """Cleanup resources."""
        self.memory.close()


# Singleton instance
_agent_instance: Optional[ResearchAgent] = None


def get_agent() -> ResearchAgent:
    """Get or create the agent singleton."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ResearchAgent()
    return _agent_instance

