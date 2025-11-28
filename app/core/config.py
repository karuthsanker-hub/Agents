"""
Configuration Management
========================
Centralized configuration using Pydantic Settings.
Manages all environment variables for the Arctic Debate Card Agent.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Find the project root (where .env is located)
def get_project_root() -> Path:
    """
    Find the project root directory containing .env file.
    
    Traverses up from the current file location until .env is found,
    or falls back to the first_agent directory.
    
    Returns:
        Path: The project root directory path
    """
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / ".env").exists():
            return current
        current = current.parent
    # Fallback to first_agent directory
    return Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All configuration is centralized here and loaded from .env file.
    Settings are cached for performance using lru_cache.
    
    Attributes:
        openai_api_key: OpenAI API key for GPT calls
        database_url: PostgreSQL connection string
        redis_url: Redis connection string
        google_client_id: Google OAuth client ID
        google_client_secret: Google OAuth client secret
    """
    
    model_config = SettingsConfigDict(
        env_file=str(get_project_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # App Configuration
    app_name: str = "Arctic Debate Card Agent"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production-use-secrets-token"
    
    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    
    # Database Configuration
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600  # 1 hour default cache TTL
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"
    
    # Pinecone Configuration (Optional)
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "agent-knowledge"
    
    # Google OAuth Configuration
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000
    
    @property
    def is_google_auth_enabled(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(self.google_client_id and self.google_client_secret)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to avoid re-reading .env file on every call.
    
    Returns:
        Settings: The application settings instance
    """
    return Settings()

