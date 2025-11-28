"""
Authentication Module
=====================
Google OAuth2 authentication for the Arctic Debate Card Agent.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode

import httpx
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("auth")


class AuthManager:
    """
    Manages Google OAuth authentication and session handling.
    
    Features:
    - Google OAuth2 login flow
    - Session token management
    - User profile storage in PostgreSQL
    - Secure token generation
    
    Usage:
        auth = AuthManager()
        login_url = auth.get_google_login_url(redirect_uri)
        user = await auth.handle_google_callback(code, redirect_uri)
    """
    
    def __init__(self):
        """Initialize the AuthManager with Google OAuth settings."""
        self.settings = get_settings()
        self._sessions: Dict[str, Dict[str, Any]] = {}  # In-memory session store
        self._init_database()
        logger.info("AuthManager initialized")
    
    def _get_connection(self):
        """Get a PostgreSQL database connection."""
        import psycopg2
        return psycopg2.connect(self.settings.database_url)
    
    def _init_database(self):
        """Initialize the users table in PostgreSQL."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Users table for storing Google account info
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        google_id VARCHAR(255) UNIQUE NOT NULL,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        name VARCHAR(255),
                        picture_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_admin BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # User sessions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        is_valid BOOLEAN DEFAULT TRUE
                    )
                """)
                
                conn.commit()
                logger.info("Auth database tables initialized")
        except Exception as e:
            logger.error(f"Failed to initialize auth database: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_google_login_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """
        Generate the Google OAuth login URL.
        
        Args:
            redirect_uri: The callback URL after authentication
            state: Optional state parameter for CSRF protection
            
        Returns:
            The Google OAuth authorization URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self._sessions[f"state_{state}"] = {
            "created_at": datetime.now(),
            "redirect_uri": redirect_uri
        }
        
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        logger.info(f"Generated Google login URL for redirect: {redirect_uri}")
        return url
    
    async def handle_google_callback(
        self, 
        code: str, 
        redirect_uri: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle the Google OAuth callback and exchange code for tokens.
        
        Args:
            code: The authorization code from Google
            redirect_uri: The redirect URI used in the initial request
            state: The state parameter (used for return URL, not strict validation)
            
        Returns:
            User info dictionary with session token
        """
        logger.info("=" * 50)
        logger.info("Processing Google OAuth callback")
        logger.info(f"Code: {code[:20]}..." if code else "No code")
        logger.info(f"Redirect URI: {redirect_uri}")
        logger.info(f"State: {state}")
        logger.info("=" * 50)
        
        # Note: We use state for return URL, so don't strictly validate it
        # Just clean up if it exists in our sessions
        if state:
            state_key = f"state_{state}"
            if state_key in self._sessions:
                del self._sessions[state_key]
                logger.debug(f"Cleaned up state: {state_key}")
        
        try:
            logger.info("Exchanging authorization code for tokens...")
            
            # Exchange code for tokens
            async with httpx.AsyncClient(timeout=30.0) as client:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )
                
                logger.info(f"Token response status: {token_response.status_code}")
                
                if token_response.status_code != 200:
                    error_detail = token_response.text
                    logger.error(f"Token exchange failed!")
                    logger.error(f"Status: {token_response.status_code}")
                    logger.error(f"Response: {error_detail}")
                    
                    # Try to parse error
                    try:
                        error_json = token_response.json()
                        error_msg = error_json.get('error_description', error_json.get('error', 'Unknown error'))
                        return {"error": f"Google auth failed: {error_msg}"}
                    except:
                        return {"error": f"Token exchange failed (HTTP {token_response.status_code})"}
                
                tokens = token_response.json()
                access_token = tokens.get("access_token")
                logger.info(f"✅ Access token received (length: {len(access_token) if access_token else 0})")
                
                # Get user info from Google
                logger.info("Fetching user info from Google...")
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                logger.info(f"User info response status: {user_response.status_code}")
                
                if user_response.status_code != 200:
                    logger.error(f"Failed to get user info: {user_response.text}")
                    return {"error": "Failed to get user info from Google"}
                
                google_user = user_response.json()
                
            # Create or update user in database
            user = self._upsert_user(google_user)
            
            # Create session token
            session_token = self._create_session(user["id"])
            
            logger.info(f"User logged in: {user['email']}")
            
            return {
                "success": True,
                "user": user,
                "session_token": session_token
            }
            
        except Exception as e:
            logger.error(f"OAuth callback error: {e}")
            return {"error": str(e)}
    
    def _upsert_user(self, google_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update user record from Google profile.
        
        Args:
            google_user: User info from Google API
            
        Returns:
            User dictionary with database ID
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Try to update existing user
                cur.execute("""
                    INSERT INTO users (google_id, email, name, picture_url, last_login)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (google_id) DO UPDATE
                    SET name = EXCLUDED.name,
                        picture_url = EXCLUDED.picture_url,
                        last_login = CURRENT_TIMESTAMP
                    RETURNING id, google_id, email, name, picture_url, is_admin
                """, (
                    google_user.get("id"),
                    google_user.get("email"),
                    google_user.get("name"),
                    google_user.get("picture")
                ))
                
                row = cur.fetchone()
                conn.commit()
                
                return {
                    "id": row[0],
                    "google_id": row[1],
                    "email": row[2],
                    "name": row[3],
                    "picture_url": row[4],
                    "is_admin": row[5]
                }
        finally:
            conn.close()
    
    def _create_session(self, user_id: int, days_valid: int = 7) -> str:
        """
        Create a new session token for a user.
        
        Args:
            user_id: The database user ID
            days_valid: Number of days the session is valid
            
        Returns:
            The session token string
        """
        token = secrets.token_urlsafe(64)
        expires_at = datetime.now() + timedelta(days=days_valid)
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Invalidate old sessions for this user
                cur.execute(
                    "UPDATE user_sessions SET is_valid = FALSE WHERE user_id = %s",
                    (user_id,)
                )
                
                # Create new session
                cur.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (%s, %s, %s)
                """, (user_id, token, expires_at))
                
                conn.commit()
                
            logger.info(f"Created session for user {user_id}")
            return token
        finally:
            conn.close()
    
    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate a session token and return user info.
        
        Args:
            token: The session token to validate
            
        Returns:
            User dictionary if valid, None otherwise
        """
        if not token:
            return None
        
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.id, u.email, u.name, u.picture_url, u.is_admin
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_token = %s 
                      AND s.is_valid = TRUE 
                      AND s.expires_at > CURRENT_TIMESTAMP
                      AND u.is_active = TRUE
                """, (token,))
                
                row = cur.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "email": row[1],
                        "name": row[2],
                        "picture_url": row[3],
                        "is_admin": row[4]
                    }
                return None
        finally:
            conn.close()
    
    def logout(self, token: str) -> bool:
        """
        Invalidate a session token.
        
        Args:
            token: The session token to invalidate
            
        Returns:
            True if successful
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_sessions SET is_valid = FALSE WHERE session_token = %s",
                    (token,)
                )
                conn.commit()
                logger.info("User logged out")
                return True
        finally:
            conn.close()
    
    def get_all_users(self) -> list:
        """Get all registered users (admin only)."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, email, name, picture_url, created_at, last_login, is_admin
                    FROM users WHERE is_active = TRUE
                    ORDER BY last_login DESC
                """)
                return [
                    {
                        "id": row[0],
                        "email": row[1],
                        "name": row[2],
                        "picture_url": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                        "last_login": row[5].isoformat() if row[5] else None,
                        "is_admin": row[6]
                    }
                    for row in cur.fetchall()
                ]
        finally:
            conn.close()


# Singleton instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get singleton AuthManager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager

