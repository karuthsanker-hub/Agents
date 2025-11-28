"""
Security Module
===============
Authentication dependencies and security utilities for FastAPI.

SECURITY FEATURES:
- Optional and required authentication dependencies
- Session validation from cookies
- Admin-only access control

Author: Shiv Sanker
"""

from typing import Optional
from fastapi import Request, HTTPException, Depends
from app.core.auth import get_auth_manager
from app.core.logging_config import get_logger

logger = get_logger("security")


# ==================== Authentication Dependencies ====================

async def get_current_user_optional(request: Request) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    
    Use this for endpoints that work for both authenticated and anonymous users,
    but may provide enhanced functionality for authenticated users.
    """
    token = request.cookies.get("session_token")
    
    if not token:
        return None
    
    auth = get_auth_manager()
    user = auth.validate_session(token)
    return user


async def get_current_user(request: Request) -> dict:
    """
    Require authentication - returns user or raises 401.
    
    Use this dependency for endpoints that MUST be authenticated.
    
    Usage:
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"message": f"Hello {user['email']}"}
    """
    user = await get_current_user_optional(request)
    
    if not user:
        logger.warning(f"Unauthorized access attempt: {request.url.path}")
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_admin_user(request: Request) -> dict:
    """
    Require admin authentication - returns user or raises 401/403.
    
    Use this for admin-only endpoints.
    """
    user = await get_current_user(request)
    
    if not user.get("is_admin"):
        logger.warning(f"Non-admin access attempt: {user['email']} -> {request.url.path}")
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return user


# ==================== Rate Limiting Check ====================

async def check_api_rate_limit(request: Request):
    """
    Check if API rate limits are exceeded.
    
    Use as a dependency to protect expensive endpoints.
    """
    from app.core.admin_config import get_admin_config
    
    admin = get_admin_config()
    rate_check = admin.check_rate_limit()
    
    if not rate_check.get('allowed', True):
        logger.warning(f"Rate limit exceeded: {rate_check.get('reason')}")
        raise HTTPException(
            status_code=429,
            detail=rate_check.get('reason', 'Rate limit exceeded')
        )


# ==================== Combined Dependencies ====================

async def require_auth_and_rate_limit(
    request: Request,
    user: dict = Depends(get_current_user)
) -> dict:
    """
    Require both authentication AND check rate limits.
    
    Use for expensive endpoints that call OpenAI.
    """
    await check_api_rate_limit(request)
    return user

