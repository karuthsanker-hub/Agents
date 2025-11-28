"""
System Router
=============
System endpoints for health checks, stats, and database info.

SECURITY:
- Health checks are public (needed for monitoring)
- Database info requires authentication

Author: Shiv Sanker
"""

from fastapi import APIRouter, Depends
from app.agent import get_agent
from app.core.logging_config import api_logger as logger
from app.core.security import get_current_user

router = APIRouter(tags=["System"])


@router.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "service": "Arctic Debate Card Agent",
        "version": "2.0.0"
    }


@router.get("/health")
async def health_check():
    """Detailed health check."""
    logger.info("Health check requested")
    
    health = {
        "status": "healthy",
        "services": {}
    }
    
    # Check agent
    try:
        agent = get_agent()
        health["services"]["agent"] = "ok"
        health["services"]["model"] = agent.model
    except Exception as e:
        health["services"]["agent"] = f"error: {e}"
        health["status"] = "degraded"
    
    return health


@router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """
    Get agent statistics.
    
    REQUIRES AUTHENTICATION.
    """
    logger.info(f"Stats requested by {user['email']}")
    agent = get_agent()
    return agent.get_stats()


@router.get("/db-info")
async def get_db_info(user: dict = Depends(get_current_user)):
    """
    Get detailed information about all databases.
    
    REQUIRES AUTHENTICATION.
    """
    logger.info(f"Database info requested by {user['email']}")
    
    agent = get_agent()
    memory = agent.memory
    
    # PostgreSQL info
    pg_info = {"status": "disconnected", "tables": 0, "total_rows": 0}
    try:
        with memory.pg_conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM conversations;")
            conv_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(DISTINCT session_id) FROM conversations;")
            session_count = cur.fetchone()[0]
            
            # Article count
            cur.execute("SELECT COUNT(*) FROM articles;")
            article_count = cur.fetchone()[0]
            
            pg_info = {
                "status": "connected",
                "version": version.split(",")[0],
                "conversations": conv_count,
                "sessions": session_count,
                "articles": article_count,
                "tables": ["conversations", "agent_stats", "articles", "debate_cards"]
            }
    except Exception as e:
        pg_info["error"] = str(e)
    
    # Redis info
    redis_info = {"status": "disconnected"}
    try:
        info = memory.redis.info()
        keys = memory.redis.dbsize()
        redis_info = {
            "status": "connected",
            "version": info.get("redis_version", "unknown"),
            "keys": keys,
            "memory_used": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 1)
        }
    except Exception as e:
        redis_info["error"] = str(e)
    
    # ChromaDB info
    chroma_info = {"status": "disconnected"}
    try:
        collections = memory.chroma.list_collections()
        total_docs = sum(c.count() for c in collections)
        chroma_info = {
            "status": "connected",
            "type": "Local (PersistentClient)",
            "path": memory.settings.chroma_persist_dir,
            "collections": len(collections),
            "total_documents": total_docs,
            "collection_names": [c.name for c in collections]
        }
    except Exception as e:
        chroma_info["error"] = str(e)
    
    # Pinecone info
    pinecone_info = {"status": "not configured"}
    if memory.settings.pinecone_api_key:
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=memory.settings.pinecone_api_key)
            indexes = pc.list_indexes()
            pinecone_info = {
                "status": "connected",
                "type": "Cloud (Serverless)",
                "indexes": len(list(indexes)),
                "index_names": [idx.name for idx in indexes],
                "environment": memory.settings.pinecone_environment or "default"
            }
        except Exception as e:
            pinecone_info = {"status": "error", "error": str(e)}
    
    return {
        "postgresql": pg_info,
        "redis": redis_info,
        "chromadb": chroma_info,
        "pinecone": pinecone_info
    }

