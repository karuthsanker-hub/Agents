"""
API Routers
===========
FastAPI route modules for the Arctic Debate Card Agent.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

from .chat import router as chat_router
from .articles import router as articles_router
from .system import router as system_router
from .admin import router as admin_router
from .auth import router as auth_router

__all__ = [
    "chat_router", 
    "articles_router", 
    "system_router", 
    "admin_router",
    "auth_router"
]

