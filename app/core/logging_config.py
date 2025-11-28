"""
Logging Configuration
=====================
Centralized logging setup for the Debate Card Agent.
Provides colored console output, file logging, and structured logging utilities.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with colors for console output.
    
    Uses ANSI escape codes for terminal coloring:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta
    """
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname:8}{self.RESET}"
        record.name = f"\033[94m{record.name}\033[0m"  # Blue for logger name
        return super().format(record)


class VerboseLogger:
    """
    Wrapper for verbose logging with structured data support.
    
    Provides methods for logging API requests, responses, and errors
    with consistent formatting and optional JSON serialization.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def request(self, method: str, path: str, data: Any = None, **kwargs):
        """Log an incoming request with optional body data."""
        msg = f"➡️  REQUEST: {method} {path}"
        if data:
            try:
                data_str = json.dumps(data, default=str)[:500]
                msg += f" | Body: {data_str}"
            except:
                pass
        for key, value in kwargs.items():
            msg += f" | {key}: {value}"
        self.logger.info(msg)
    
    def response(self, status: int, data: Any = None, time_ms: float = None, **kwargs):
        """Log an outgoing response."""
        emoji = "✅" if status < 400 else "❌"
        msg = f"{emoji} RESPONSE: {status}"
        if time_ms:
            msg += f" ({time_ms:.1f}ms)"
        if data and isinstance(data, dict):
            try:
                # Only log a preview of response data
                preview = {k: str(v)[:100] for k, v in list(data.items())[:5]}
                msg += f" | {json.dumps(preview)}"
            except:
                pass
        self.logger.info(msg)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log an error with exception details."""
        msg = f"❌ ERROR: {message}"
        if error:
            msg += f" | Exception: {type(error).__name__}: {str(error)}"
        for key, value in kwargs.items():
            msg += f" | {key}: {value}"
        self.logger.error(msg)
    
    def cache_hit(self, key: str, source: str = "redis"):
        """Log a cache hit."""
        self.logger.debug(f"💾 CACHE HIT: {source} | Key: {key[:50]}")
    
    def cache_miss(self, key: str, source: str = "redis"):
        """Log a cache miss."""
        self.logger.debug(f"💨 CACHE MISS: {source} | Key: {key[:50]}")
    
    def db_query(self, operation: str, table: str, time_ms: float = None):
        """Log a database operation."""
        msg = f"🗃️  DB: {operation} on {table}"
        if time_ms:
            msg += f" ({time_ms:.1f}ms)"
        self.logger.debug(msg)
    
    def token_usage(self, tokens: int, endpoint: str, model: str = None):
        """Log OpenAI token usage."""
        msg = f"🔢 TOKENS: {tokens:,} | Endpoint: {endpoint}"
        if model:
            msg += f" | Model: {model}"
        self.logger.info(msg)


def setup_logging(
    name: str = "debate_agent",
    level: int = logging.DEBUG,  # Changed to DEBUG for verbose logging
    log_file: bool = True
) -> logging.Logger:
    """
    Set up logging with console and optional file output.
    
    Args:
        name: Logger name (will be prefixed with 'debate.')
        level: Logging level (default: DEBUG for verbose output)
        log_file: Whether to also log to file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter(
        '%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (no colors, more detailed)
    if log_file:
        log_filename = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always verbose in file
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'api', 'database')
        
    Returns:
        Configured logger for the module
    """
    return setup_logging(f"debate.{module_name}")


def get_verbose_logger(module_name: str) -> VerboseLogger:
    """
    Get a verbose logger with structured logging methods.
    
    Args:
        module_name: Name of the module
        
    Returns:
        VerboseLogger instance with helper methods
    """
    return VerboseLogger(get_logger(module_name))


# Pre-configured loggers for different modules
api_logger = get_logger("api")
db_logger = get_logger("database")
analyzer_logger = get_logger("analyzer")
agent_logger = get_logger("agent")
cache_logger = get_logger("cache")
auth_logger = get_logger("auth")

# Verbose loggers for detailed tracking
verbose_api = get_verbose_logger("api.verbose")
verbose_db = get_verbose_logger("db.verbose")

