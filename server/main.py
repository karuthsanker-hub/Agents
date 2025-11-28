"""
Arctic Debate Card Agent - API Server
=====================================
Modular FastAPI server for debate research and card cutting.

Author: Shiv Sanker
Created: 2024
License: MIT

Routers:
- /auth - Google OAuth authentication
- /chat - Research Assistant chat
- /articles - Article management
- /admin - Admin configuration
- System endpoints (/, /health, /stats, /db-info)
"""

import sys
import os
import time
import json
from typing import Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.logging_config import setup_logging, api_logger as logger
from app.core.config import get_settings

# Import routers
from server.routers import (
    chat_router, 
    articles_router, 
    system_router, 
    admin_router,
    auth_router
)
from server.ui_templates import get_main_ui

# ==================== Setup Logging ====================

setup_logging("debate_agent")
logger.info("Starting Arctic Debate Card Agent API Server")

# ==================== FastAPI App ====================

# SECURITY: Disable API docs in production
settings_for_docs = get_settings()
docs_url = "/docs" if settings_for_docs.debug else None
redoc_url = "/redoc" if settings_for_docs.debug else None

app = FastAPI(
    title="Arctic Debate Card Agent",
    description="AI-powered research assistant for Policy Debate (2025-2026 Arctic Topic)",
    version="2.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url
)

# CORS middleware - SECURITY: Restrict origins in production
settings = get_settings()

# Define allowed origins based on environment
if settings.app_env == "production":
    # In production, only allow specific origins
    allowed_origins = [
        "https://yourdomain.com",  # Update with your actual domain
    ]
else:
    # In development, allow localhost
    allowed_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # If using separate frontend
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


# ==================== Verbose Logging Middleware ====================

@app.middleware("http")
async def verbose_logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for verbose request/response logging.
    
    Logs:
    - Request method, path, query params
    - Request body (for POST/PUT)
    - Response status code
    - Response time in milliseconds
    - Any errors that occur
    """
    start_time = time.time()
    request_id = f"{int(start_time * 1000) % 100000:05d}"
    
    # Log request details
    method = request.method
    path = request.url.path
    query = str(request.query_params) if request.query_params else ""
    
    # Only log for API endpoints, not static resources
    is_api_call = not path.endswith(('.js', '.css', '.ico', '.png', '.jpg'))
    
    if is_api_call:
        logger.info(f"[{request_id}] ➡️  {method} {path} {query}")
        
        # Log request body for POST/PUT (excluding large payloads)
        if method in ("POST", "PUT") and request.headers.get("content-type", "").startswith("application/json"):
            try:
                body = await request.body()
                if len(body) < 2000:  # Don't log huge payloads
                    body_preview = body.decode('utf-8')[:500]
                    logger.debug(f"[{request_id}] 📥 Body: {body_preview}")
            except:
                pass
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate response time
        process_time = (time.time() - start_time) * 1000
        
        if is_api_call:
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(f"[{request_id}] {status_emoji} {response.status_code} ({process_time:.1f}ms)")
        
        # Add timing header
        response.headers["X-Process-Time-Ms"] = f"{process_time:.1f}"
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] ❌ Error: {str(e)} ({process_time:.1f}ms)")
        raise


# ==================== Include Routers ====================

# Authentication routes (/auth/*)
app.include_router(auth_router)

# System routes (/, /health, /stats, /db-info)
app.include_router(system_router)

# Chat routes (/chat, /chat/search, /chat/history)
app.include_router(chat_router)

# Article routes (/articles/*)
app.include_router(articles_router)

# Admin routes (/admin/*)
app.include_router(admin_router)

logger.info("All routers loaded successfully")

# ==================== Web UI ====================

@app.get("/ui", response_class=HTMLResponse)
async def web_ui(request: Request):
    """
    Arctic Debate Card Agent web interface.
    
    Serves the main SPA with authentication state.
    """
    logger.info("UI accessed")
    return get_main_ui()


# ==================== Startup/Shutdown ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    settings = get_settings()
    
    logger.info("=" * 60)
    logger.info("🧊 Arctic Debate Card Agent Starting...")
    logger.info("=" * 60)
    logger.info("Resolution: The USFG should significantly increase")
    logger.info("            its exploration and/or development of the Arctic")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug Mode:  {settings.debug}")
    logger.info(f"OpenAI Model: {settings.openai_model}")
    logger.info(f"Google Auth: {'Enabled' if settings.is_google_auth_enabled else 'Disabled'}")
    logger.info("=" * 60)
    logger.info("Endpoints:")
    logger.info("  API Docs:   http://127.0.0.1:8000/docs")
    logger.info("  Web UI:     http://127.0.0.1:8000/ui")
    logger.info("  Admin:      http://127.0.0.1:8000/admin/ui")
    logger.info("  Auth:       http://127.0.0.1:8000/auth/login")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Server shutting down...")


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
