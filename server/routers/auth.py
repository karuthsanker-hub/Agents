"""
Authentication Router
=====================
Handles Google OAuth login/logout and session management.
Includes dedicated login page with debugging support.

Author: Shiv Sanker
Created: 2024
License: MIT
"""

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional
from urllib.parse import urlencode, quote

from app.core.config import get_settings
from app.core.auth import get_auth_manager
from app.core.logging_config import get_logger

logger = get_logger("auth.router")
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== Models ====================

class TokenValidation(BaseModel):
    """Response model for token validation."""
    valid: bool
    user: Optional[dict] = None


# ==================== Login Page ====================

def get_login_page_html(error: str = None, return_url: str = "/ui") -> str:
    """Generate the dedicated login page HTML."""
    error_html = f'<div class="error-msg">❌ {error}</div>' if error else ''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Arctic Debate Card Agent</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #0f1419 0%, #1a2744 50%, #0f1419 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #e8e8e8;
        }}
        
        .login-container {{
            background: rgba(26, 31, 46, 0.95);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 48px;
            max-width: 420px;
            width: 90%;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }}
        
        .logo {{
            font-size: 3.5rem;
            margin-bottom: 16px;
        }}
        
        h1 {{
            font-size: 1.8rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: #888;
            margin-bottom: 32px;
            font-size: 0.95rem;
        }}
        
        .google-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            padding: 14px 24px;
            background: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 500;
            color: #333;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }}
        
        .google-btn:hover {{
            background: #f8f8f8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        .google-btn img {{
            width: 20px;
            height: 20px;
        }}
        
        .error-msg {{
            background: rgba(255,107,107,0.15);
            border: 1px solid rgba(255,107,107,0.3);
            color: #ff6b6b;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            font-size: 0.9rem;
        }}
        
        .info-box {{
            background: rgba(0,217,255,0.1);
            border: 1px solid rgba(0,217,255,0.2);
            border-radius: 8px;
            padding: 16px;
            margin-top: 24px;
            text-align: left;
            font-size: 0.85rem;
        }}
        
        .info-box h3 {{
            color: #00d9ff;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }}
        
        .info-box ul {{
            margin-left: 16px;
            color: #aaa;
        }}
        
        .info-box li {{
            margin: 4px 0;
        }}
        
        .back-link {{
            display: inline-block;
            margin-top: 24px;
            color: #888;
            text-decoration: none;
            font-size: 0.9rem;
        }}
        
        .back-link:hover {{
            color: #00d9ff;
        }}
        
        .debug-panel {{
            margin-top: 24px;
            padding: 16px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            text-align: left;
            font-family: monospace;
            font-size: 0.75rem;
            color: #888;
        }}
        
        .debug-panel .label {{
            color: #00ff88;
        }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">🧊</div>
        <h1>Arctic Debate Agent</h1>
        <p class="subtitle">Sign in to access research tools</p>
        
        {error_html}
        
        <a href="/auth/google?return_url={quote(return_url)}" class="google-btn" id="googleLoginBtn" onclick="handleLogin()">
            <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google">
            <span>Sign in with Google</span>
        </a>
        
        <div class="info-box">
            <h3>🔐 Secure Authentication</h3>
            <ul>
                <li>Uses Google OAuth 2.0</li>
                <li>No password stored locally</li>
                <li>Session expires in 7 days</li>
            </ul>
        </div>
        
        <a href="/ui" class="back-link">← Continue without signing in</a>
        
        <div class="debug-panel" id="debugPanel">
            <div><span class="label">Return URL:</span> {return_url}</div>
            <div><span class="label">Status:</span> <span id="debugStatus">Ready</span></div>
            <div><span class="label">Time:</span> <span id="debugTime"></span></div>
        </div>
    </div>
    
    <script>
        console.log('🧊 [Auth] Login page loaded');
        console.log('🧊 [Auth] Return URL:', '{return_url}');
        
        document.getElementById('debugTime').textContent = new Date().toISOString();
        
        function handleLogin() {{
            console.log('🧊 [Auth] Google login button clicked');
            document.getElementById('debugStatus').textContent = 'Redirecting to Google...';
            
            // Store return URL in sessionStorage for after callback
            sessionStorage.setItem('auth_return_url', '{return_url}');
            console.log('🧊 [Auth] Stored return URL in sessionStorage');
        }}
        
        // Check for errors in URL
        const urlParams = new URLSearchParams(window.location.search);
        const error = urlParams.get('error');
        if (error) {{
            console.error('🧊 [Auth] Error from URL:', error);
            document.getElementById('debugStatus').textContent = 'Error: ' + error;
        }}
        
        // Log auth configuration status
        fetch('/auth/status')
            .then(r => r.json())
            .then(data => {{
                console.log('🧊 [Auth] Status:', data);
                if (!data.google_enabled) {{
                    document.getElementById('debugStatus').textContent = 'ERROR: Google OAuth not configured!';
                    document.getElementById('googleLoginBtn').style.opacity = '0.5';
                    document.getElementById('googleLoginBtn').style.pointerEvents = 'none';
                }}
            }})
            .catch(e => console.error('🧊 [Auth] Status check failed:', e));
    </script>
</body>
</html>'''


# ==================== Endpoints ====================

@router.get("/status")
async def auth_status():
    """
    Check if authentication is enabled and configured.
    
    Returns:
        dict: Status of Google OAuth configuration
    """
    settings = get_settings()
    logger.info(f"Auth status check - Google enabled: {settings.is_google_auth_enabled}")
    logger.info(f"Client ID configured: {bool(settings.google_client_id)}")
    logger.info(f"Client Secret configured: {bool(settings.google_client_secret)}")
    
    return {
        "google_enabled": settings.is_google_auth_enabled,
        "login_url": "/auth/page" if settings.is_google_auth_enabled else None,
        "client_id_set": bool(settings.google_client_id),
        "client_secret_set": bool(settings.google_client_secret)
    }


@router.get("/page", response_class=HTMLResponse)
async def login_page(
    request: Request,
    return_url: str = "/ui",
    error: Optional[str] = None
):
    """
    Dedicated login page.
    
    Args:
        return_url: URL to redirect to after successful login
        error: Error message to display
    """
    logger.info(f"Login page accessed - return_url: {return_url}")
    return get_login_page_html(error=error, return_url=return_url)


@router.get("/google")
async def google_login(request: Request, return_url: str = "/ui"):
    """
    Initiate Google OAuth login flow.
    
    Redirects user to Google's authorization page.
    On success, Google will redirect back to /auth/callback.
    """
    settings = get_settings()
    
    logger.info("=" * 50)
    logger.info("🔐 GOOGLE LOGIN INITIATED")
    logger.info(f"Return URL: {return_url}")
    logger.info(f"Client ID: {settings.google_client_id[:20] if settings.google_client_id else 'NOT SET'}...")
    logger.info(f"Client Secret: {'SET' if settings.google_client_secret else 'NOT SET'}")
    logger.info("=" * 50)
    
    if not settings.is_google_auth_enabled:
        logger.error("Google OAuth is NOT configured!")
        return RedirectResponse(url=f"/auth/page?error=Google+OAuth+not+configured&return_url={quote(return_url)}")
    
    try:
        auth = get_auth_manager()
        
        # Build redirect URI - must match what's configured in Google Console
        redirect_uri = str(request.url_for("google_callback"))
        logger.info(f"Redirect URI: {redirect_uri}")
        
        # Store return URL in state (encoded)
        state_data = return_url
        
        # Get Google login URL
        login_url = auth.get_google_login_url(redirect_uri, state=state_data)
        
        logger.info(f"Google OAuth URL generated (first 100 chars): {login_url[:100]}...")
        logger.info("Redirecting to Google...")
        
        return RedirectResponse(url=login_url)
        
    except Exception as e:
        logger.error(f"Error initiating Google login: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return RedirectResponse(url=f"/auth/page?error={quote(str(e))}&return_url={quote(return_url)}")


@router.get("/login")
async def login_redirect(request: Request, return_url: str = "/ui"):
    """Redirect /auth/login to the login page."""
    return RedirectResponse(url=f"/auth/page?return_url={quote(return_url)}")


@router.get("/callback", name="google_callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """
    Handle Google OAuth callback.
    
    After user authenticates with Google, this endpoint receives
    the authorization code and exchanges it for user info.
    """
    logger.info("=" * 50)
    logger.info("🔐 GOOGLE CALLBACK RECEIVED")
    logger.info(f"Code received: {bool(code)}")
    logger.info(f"State: {state}")
    logger.info(f"Error: {error}")
    logger.info(f"Error description: {error_description}")
    logger.info("=" * 50)
    
    # Determine return URL from state
    return_url = state if state and state.startswith('/') else "/ui"
    
    if error:
        logger.error(f"OAuth error from Google: {error} - {error_description}")
        return RedirectResponse(url=f"/auth/page?error={quote(error_description or error)}&return_url={quote(return_url)}")
    
    if not code:
        logger.error("No authorization code received")
        return RedirectResponse(url=f"/auth/page?error=No+authorization+code&return_url={quote(return_url)}")
    
    try:
        auth = get_auth_manager()
        redirect_uri = str(request.url_for("google_callback"))
        
        logger.info(f"Exchanging code for tokens...")
        logger.info(f"Redirect URI for token exchange: {redirect_uri}")
        
        # Exchange code for user info
        result = await auth.handle_google_callback(code, redirect_uri, state)
        
        logger.info(f"Token exchange result: {list(result.keys())}")
        
        if "error" in result:
            logger.error(f"OAuth callback failed: {result['error']}")
            return RedirectResponse(url=f"/auth/page?error={quote(result['error'])}&return_url={quote(return_url)}")
        
        # Set session cookie and redirect
        user = result["user"]
        token = result["session_token"]
        
        logger.info(f"✅ User authenticated: {user['email']}")
        logger.info(f"Redirecting to: {return_url}")
        
        response = RedirectResponse(url=f"{return_url}?auth_success=true")
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Exception in callback: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return RedirectResponse(url=f"/auth/page?error={quote(str(e))}&return_url={quote(return_url)}")


@router.get("/logout")
async def logout(request: Request, return_url: str = "/ui"):
    """
    Log out the current user.
    
    Invalidates the session token and clears the cookie.
    """
    token = request.cookies.get("session_token")
    
    if token:
        try:
            auth = get_auth_manager()
            auth.logout(token)
            logger.info("User logged out successfully")
        except Exception as e:
            logger.error(f"Error during logout: {e}")
    
    response = RedirectResponse(url=return_url)
    response.delete_cookie("session_token")
    
    return response


@router.get("/me")
async def get_current_user(request: Request):
    """
    Get the current authenticated user's info.
    
    Returns:
        dict: User info if authenticated, or error if not
    """
    token = request.cookies.get("session_token")
    
    if not token:
        logger.debug("No session token in request")
        return {"authenticated": False}
    
    auth = get_auth_manager()
    user = auth.validate_session(token)
    
    if user:
        logger.debug(f"Session validated for: {user['email']}")
        return {
            "authenticated": True,
            "user": user
        }
    
    logger.debug("Invalid or expired session token")
    return {"authenticated": False}


@router.post("/validate")
async def validate_token(request: Request):
    """
    Validate a session token from cookie or header.
    
    Checks both cookie and Authorization header for the token.
    
    Returns:
        TokenValidation: Whether token is valid and user info
    """
    # Check cookie first
    token = request.cookies.get("session_token")
    
    # Then check header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        return TokenValidation(valid=False)
    
    auth = get_auth_manager()
    user = auth.validate_session(token)
    
    if user:
        return TokenValidation(valid=True, user=user)
    
    return TokenValidation(valid=False)


@router.get("/users")
async def list_users(request: Request):
    """
    List all registered users (admin only).
    
    Requires admin privileges to access.
    """
    token = request.cookies.get("session_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    auth = get_auth_manager()
    user = auth.validate_session(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = auth.get_all_users()
    logger.info(f"Admin {user['email']} listed all users")
    
    return {"users": users}

