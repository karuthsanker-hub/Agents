"""
Admin Configuration Manager
============================
Manages admin settings, usage limits, and authentication.
Stores configuration securely in PostgreSQL.
"""

import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("admin")

# Default configuration values
DEFAULT_CONFIG = {
    "daily_token_limit": 100000,      # 100k tokens per day
    "monthly_token_limit": 2000000,   # 2M tokens per month
    "max_requests_per_minute": 20,    # Rate limit
    "max_tokens_per_request": 4000,   # Max tokens per single request
    "enable_rate_limiting": True,
    "enable_usage_tracking": True,
}

# Default admin password
DEFAULT_ADMIN_PASSWORD = "Pass@1234"


class AdminConfigManager:
    """Manages admin configuration and usage tracking."""
    
    def __init__(self):
        self.settings = get_settings()
        self._init_database()
        logger.info("AdminConfigManager initialized")
    
    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.settings.database_url)
    
    def _init_database(self):
        """Initialize admin tables in the database."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Admin config table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_config (
                        key VARCHAR(100) PRIMARY KEY,
                        value TEXT NOT NULL,
                        description TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Admin authentication table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS admin_auth (
                        id SERIAL PRIMARY KEY,
                        password_hash VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP
                    )
                """)
                
                # Usage tracking table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usage_tracking (
                        id SERIAL PRIMARY KEY,
                        session_id VARCHAR(100),
                        endpoint VARCHAR(100) NOT NULL,
                        tokens_used INTEGER NOT NULL,
                        model VARCHAR(50),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Daily usage summary table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usage_summary (
                        date DATE PRIMARY KEY,
                        total_tokens INTEGER DEFAULT 0,
                        total_requests INTEGER DEFAULT 0,
                        unique_sessions INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
                
                # Initialize default config if not exists
                self._init_default_config(cur, conn)
                
                # Initialize admin password if not exists
                self._init_admin_password(cur, conn)
                
        finally:
            conn.close()
    
    def _init_default_config(self, cur, conn):
        """Initialize default configuration values."""
        for key, value in DEFAULT_CONFIG.items():
            cur.execute("""
                INSERT INTO admin_config (key, value, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (key) DO NOTHING
            """, (key, str(value), f"Default {key}"))
        conn.commit()
    
    def _init_admin_password(self, cur, conn):
        """Initialize admin password if not set."""
        cur.execute("SELECT COUNT(*) FROM admin_auth")
        if cur.fetchone()[0] == 0:
            # Hash the default password
            password_hash = bcrypt.hashpw(
                DEFAULT_ADMIN_PASSWORD.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            cur.execute(
                "INSERT INTO admin_auth (password_hash) VALUES (%s)",
                (password_hash,)
            )
            conn.commit()
            logger.info("Admin password initialized with default")
    
    def verify_admin_password(self, password: str) -> bool:
        """Verify the admin password."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM admin_auth ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                if row:
                    stored_hash = row[0].encode('utf-8')
                    result = bcrypt.checkpw(password.encode('utf-8'), stored_hash)
                    if result:
                        # Update last login
                        cur.execute("UPDATE admin_auth SET last_login = CURRENT_TIMESTAMP")
                        conn.commit()
                    return result
                return False
        finally:
            conn.close()
    
    def change_admin_password(self, new_password: str) -> bool:
        """Change the admin password."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                password_hash = bcrypt.hashpw(
                    new_password.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                cur.execute("""
                    UPDATE admin_auth 
                    SET password_hash = %s, created_at = CURRENT_TIMESTAMP
                    WHERE id = (SELECT id FROM admin_auth ORDER BY id DESC LIMIT 1)
                """, (password_hash,))
                conn.commit()
                logger.info("Admin password changed")
                return True
        except Exception as e:
            logger.error(f"Failed to change password: {e}")
            return False
        finally:
            conn.close()
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT value FROM admin_config WHERE key = %s", (key,))
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()
    
    def get_config_int(self, key: str, default: int = 0) -> int:
        """Get a configuration value as integer."""
        value = self.get_config(key)
        try:
            return int(value) if value else default
        except ValueError:
            return default
    
    def get_config_bool(self, key: str, default: bool = False) -> bool:
        """Get a configuration value as boolean."""
        value = self.get_config(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def set_config(self, key: str, value: str, description: str = None) -> bool:
        """Set a configuration value."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO admin_config (key, value, description, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (key) DO UPDATE 
                    SET value = %s, updated_at = CURRENT_TIMESTAMP
                """, (key, str(value), description, str(value)))
                conn.commit()
                logger.info(f"Config updated: {key} = {value}")
                return True
        except Exception as e:
            logger.error(f"Failed to set config: {e}")
            return False
        finally:
            conn.close()
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration values."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT key, value, description, updated_at FROM admin_config ORDER BY key")
                rows = cur.fetchall()
                return {row['key']: {
                    'value': row['value'],
                    'description': row['description'],
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                } for row in rows}
        finally:
            conn.close()
    
    def track_usage(self, endpoint: str, tokens_used: int, session_id: str = None, model: str = None):
        """Track API usage."""
        if not self.get_config_bool('enable_usage_tracking', True):
            return
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Insert usage record
                cur.execute("""
                    INSERT INTO usage_tracking (session_id, endpoint, tokens_used, model)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, endpoint, tokens_used, model))
                
                # Update daily summary
                today = datetime.now().date()
                cur.execute("""
                    INSERT INTO usage_summary (date, total_tokens, total_requests, unique_sessions)
                    VALUES (%s, %s, 1, 1)
                    ON CONFLICT (date) DO UPDATE 
                    SET total_tokens = usage_summary.total_tokens + %s,
                        total_requests = usage_summary.total_requests + 1
                """, (today, tokens_used, tokens_used))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track usage: {e}")
        finally:
            conn.close()
    
    def get_today_usage(self) -> Dict[str, int]:
        """Get today's usage statistics."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                today = datetime.now().date()
                cur.execute("""
                    SELECT total_tokens, total_requests, unique_sessions
                    FROM usage_summary WHERE date = %s
                """, (today,))
                row = cur.fetchone()
                if row:
                    return dict(row)
                return {'total_tokens': 0, 'total_requests': 0, 'unique_sessions': 0}
        finally:
            conn.close()
    
    def get_month_usage(self) -> Dict[str, int]:
        """Get this month's usage statistics."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                first_of_month = datetime.now().replace(day=1).date()
                cur.execute("""
                    SELECT COALESCE(SUM(total_tokens), 0) as total_tokens,
                           COALESCE(SUM(total_requests), 0) as total_requests
                    FROM usage_summary WHERE date >= %s
                """, (first_of_month,))
                row = cur.fetchone()
                return dict(row) if row else {'total_tokens': 0, 'total_requests': 0}
        finally:
            conn.close()
    
    def get_usage_history(self, days: int = 30) -> list:
        """Get usage history for the past N days."""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT date, total_tokens, total_requests, unique_sessions
                    FROM usage_summary 
                    WHERE date >= CURRENT_DATE - INTERVAL '%s days'
                    ORDER BY date DESC
                """, (days,))
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def check_rate_limit(self, session_id: str = None) -> Dict[str, Any]:
        """Check if rate limits are exceeded."""
        if not self.get_config_bool('enable_rate_limiting', True):
            return {'allowed': True, 'reason': 'Rate limiting disabled'}
        
        daily_limit = self.get_config_int('daily_token_limit', 100000)
        monthly_limit = self.get_config_int('monthly_token_limit', 2000000)
        
        today_usage = self.get_today_usage()
        month_usage = self.get_month_usage()
        
        if today_usage['total_tokens'] >= daily_limit:
            return {
                'allowed': False,
                'reason': f"Daily token limit reached ({today_usage['total_tokens']:,}/{daily_limit:,})",
                'limit_type': 'daily',
                'current': today_usage['total_tokens'],
                'limit': daily_limit
            }
        
        if month_usage['total_tokens'] >= monthly_limit:
            return {
                'allowed': False,
                'reason': f"Monthly token limit reached ({month_usage['total_tokens']:,}/{monthly_limit:,})",
                'limit_type': 'monthly',
                'current': month_usage['total_tokens'],
                'limit': monthly_limit
            }
        
        return {
            'allowed': True,
            'daily_remaining': daily_limit - today_usage['total_tokens'],
            'monthly_remaining': monthly_limit - month_usage['total_tokens']
        }


# Singleton instance
_admin_config: Optional[AdminConfigManager] = None

def get_admin_config() -> AdminConfigManager:
    """Get singleton AdminConfigManager instance."""
    global _admin_config
    if _admin_config is None:
        _admin_config = AdminConfigManager()
    return _admin_config

