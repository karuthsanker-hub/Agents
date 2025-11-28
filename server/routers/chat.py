"""
Chat Router
===========
Endpoints for the Research Assistant chat functionality.
Supports text attachments for document analysis.

SECURITY: All endpoints require authentication.

Author: Shiv Sanker
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import Optional, List

from app.agent import get_agent
from app.core.logging_config import api_logger as logger
from app.core.security import get_current_user, require_auth_and_rate_limit

router = APIRouter(prefix="/chat", tags=["Chat"])


# ==================== Models ====================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_cache: bool = True
    use_memory: bool = True
    attachment_text: Optional[str] = None  # For pasted text/documents


class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    session_id: str
    cached: bool = False
    response_time_ms: int = 0
    tokens_used: int = 0
    memories_used: int = 0


class SearchRequest(BaseModel):
    query: str
    n_results: int = 5


# ==================== Endpoints ====================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(require_auth_and_rate_limit)
):
    """
    Send a message to the Research Assistant.
    
    REQUIRES AUTHENTICATION (uses OpenAI API).
    
    - **message**: Your question or message
    - **session_id**: Optional session ID for conversation continuity
    - **use_cache**: Whether to use cached responses (default: true)
    - **use_memory**: Whether to search semantic memory (default: true)
    - **attachment_text**: Optional text content to analyze (pasted document, article, etc.)
    """
    logger.info(f"Chat from user: {user['email']}")
    # Combine message with attachment if provided
    full_message = request.message
    if request.attachment_text:
        # Truncate attachment if too long
        attachment = request.attachment_text[:10000]
        full_message = f"{request.message}\n\n---ATTACHED DOCUMENT---\n{attachment}\n---END DOCUMENT---"
        logger.info(f"Chat with attachment: {len(request.attachment_text)} chars")
    
    logger.info(f"Chat request: session={request.session_id}, message={request.message[:50]}...")
    
    try:
        agent = get_agent()
        result = agent.chat(
            message=full_message,
            session_id=request.session_id,
            use_cache=request.use_cache if not request.attachment_text else False,  # Don't cache attachment responses
            use_memory=request.use_memory
        )
        
        logger.info(f"Chat response: success={result.get('success')}, tokens={result.get('tokens_used', 0)}")
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            success=False,
            error=str(e),
            session_id=request.session_id or "unknown"
        )


@router.post("/search")
async def search_memories(
    request: SearchRequest,
    user: dict = Depends(get_current_user)
):
    """
    Search semantic memory for relevant past conversations.
    
    REQUIRES AUTHENTICATION.
    """
    logger.info(f"Memory search by {user['email']}: query={request.query[:50]}...")
    
    agent = get_agent()
    memories = agent.search_memories(request.query, request.n_results)
    
    logger.info(f"Memory search: found {len(memories)} results")
    return {"results": memories, "count": len(memories)}


@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    limit: int = 20,
    user: dict = Depends(get_current_user)
):
    """
    Get conversation history for a session.
    
    REQUIRES AUTHENTICATION.
    """
    logger.info(f"History request by {user['email']}: session={session_id}")
    
    # Security: Limit to reasonable range
    limit = min(max(1, limit), 100)
    
    agent = get_agent()
    history = agent.get_history(session_id, limit)
    
    return {"session_id": session_id, "history": history, "count": len(history)}

