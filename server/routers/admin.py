"""
Admin Router
============
Endpoints for admin configuration, usage monitoring, and prompt management.
Password protected admin panel with security hardening.

SECURITY FEATURES:
- HttpOnly cookies for session tokens
- Session expiration (4 hours)
- Rate limiting on login attempts
- Brute force protection

Author: Shiv Sanker
"""

import time
import secrets
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, validator

from app.core.admin_config import get_admin_config
from app.core.prompt_manager import get_prompt_manager
from app.core.logging_config import api_logger as logger
from app.core.config import get_settings

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== Security Constants ====================

SESSION_EXPIRY_HOURS = 4
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
ADMIN_COOKIE_NAME = "admin_session"


# ==================== Models ====================

class LoginRequest(BaseModel):
    password: str
    
    @validator('password')
    def password_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Password cannot be empty')
        return v


class ConfigUpdateRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    
    @validator('key')
    def key_alphanumeric(cls, v):
        # Only allow alphanumeric and underscores in config keys
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Invalid config key format')
        return v


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain a digit')
        return v


class PromptUpdateRequest(BaseModel):
    key: str
    content: str
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Prompt content cannot be empty')
        return v


# ==================== Session Management ====================

# Session store: token -> {user_id, expires_at, created_at}
_admin_sessions: Dict[str, Dict[str, Any]] = {}

# Rate limiting: IP -> {attempts, lockout_until}
_login_attempts: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"attempts": 0, "lockout_until": None})


def _get_client_ip(request: Request) -> str:
    """Get client IP for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(request: Request) -> None:
    """Check if IP is rate limited. Raises HTTPException if locked out."""
    ip = _get_client_ip(request)
    attempts = _login_attempts[ip]
    
    if attempts["lockout_until"]:
        if datetime.now() < attempts["lockout_until"]:
            remaining = (attempts["lockout_until"] - datetime.now()).seconds
            logger.warning(f"Rate limited IP attempted login: {ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many failed attempts. Try again in {remaining} seconds."
            )
        else:
            # Lockout expired, reset
            _login_attempts[ip] = {"attempts": 0, "lockout_until": None}


def _record_failed_login(request: Request) -> None:
    """Record a failed login attempt."""
    ip = _get_client_ip(request)
    _login_attempts[ip]["attempts"] += 1
    
    if _login_attempts[ip]["attempts"] >= MAX_LOGIN_ATTEMPTS:
        _login_attempts[ip]["lockout_until"] = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
        logger.warning(f"IP {ip} locked out after {MAX_LOGIN_ATTEMPTS} failed attempts")


def _clear_failed_attempts(request: Request) -> None:
    """Clear failed attempts after successful login."""
    ip = _get_client_ip(request)
    if ip in _login_attempts:
        del _login_attempts[ip]


def create_session_token() -> str:
    """Create a cryptographically secure session token."""
    return secrets.token_urlsafe(48)


def is_authenticated(request: Request) -> bool:
    """Check if request has valid admin session cookie."""
    token = request.cookies.get(ADMIN_COOKIE_NAME)
    if not token or token not in _admin_sessions:
        return False
    
    session = _admin_sessions[token]
    if datetime.now() > session["expires_at"]:
        # Session expired, clean up
        del _admin_sessions[token]
        return False
    
    return True


def get_session_token(request: Request) -> Optional[str]:
    """Extract session token from cookie."""
    return request.cookies.get(ADMIN_COOKIE_NAME)


def require_admin(request: Request) -> str:
    """Dependency to require admin authentication."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return get_session_token(request)


# Clean up expired sessions periodically
def _cleanup_expired_sessions():
    """Remove expired sessions from memory."""
    now = datetime.now()
    expired = [token for token, session in _admin_sessions.items() if now > session["expires_at"]]
    for token in expired:
        del _admin_sessions[token]


# ==================== Endpoints ====================

@router.post("/login")
async def admin_login(request: Request, login_data: LoginRequest, response: Response):
    """
    Login to admin panel.
    
    SECURITY:
    - Rate limited (5 attempts, 15 min lockout)
    - Sets HttpOnly cookie
    - Session expires in 4 hours
    """
    # Check rate limiting
    _check_rate_limit(request)
    _cleanup_expired_sessions()
    
    admin = get_admin_config()
    
    if admin.verify_admin_password(login_data.password):
        # Clear failed attempts
        _clear_failed_attempts(request)
        
        # Create session
        token = create_session_token()
        _admin_sessions[token] = {
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(hours=SESSION_EXPIRY_HOURS),
            "ip": _get_client_ip(request)
        }
        
        logger.info(f"Admin login successful from {_get_client_ip(request)}")
        
        # Set HttpOnly cookie
        settings = get_settings()
        response.set_cookie(
            key=ADMIN_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=settings.is_production,  # Only HTTPS in production
            samesite="lax",
            max_age=SESSION_EXPIRY_HOURS * 3600
        )
        
        return {
            "success": True,
            "message": "Login successful",
            "expires_in": SESSION_EXPIRY_HOURS * 3600
        }
    
    # Record failed attempt
    _record_failed_login(request)
    logger.warning(f"Admin login failed from {_get_client_ip(request)}")
    raise HTTPException(status_code=401, detail="Invalid password")


@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    """Logout from admin panel. Clears session cookie."""
    token = request.cookies.get(ADMIN_COOKIE_NAME)
    
    if token and token in _admin_sessions:
        del _admin_sessions[token]
        logger.info("Admin logged out")
    
    response.delete_cookie(ADMIN_COOKIE_NAME)
    return {"success": True, "message": "Logged out"}


@router.get("/config")
async def get_config(request: Request):
    """Get all configuration values. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    admin = get_admin_config()
    return {
        "config": admin.get_all_config(),
        "defaults": {
            "daily_token_limit": 100000,
            "monthly_token_limit": 2000000,
            "max_requests_per_minute": 20,
            "max_tokens_per_request": 4000,
            "enable_rate_limiting": True,
            "enable_usage_tracking": True,
        }
    }


@router.post("/config")
async def update_config(request: Request, config_data: ConfigUpdateRequest):
    """Update a configuration value. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    admin = get_admin_config()
    success = admin.set_config(config_data.key, config_data.value, config_data.description)
    
    if success:
        logger.info(f"Admin updated config: {config_data.key}")
        return {"success": True, "message": f"Config '{config_data.key}' updated"}
    
    raise HTTPException(status_code=500, detail="Failed to update config")


@router.post("/change-password")
async def change_password(request: Request, password_data: PasswordChangeRequest):
    """
    Change admin password. 
    
    SECURITY:
    - Requires current password verification
    - Enforces password complexity (8+ chars, upper, lower, digit)
    """
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    admin = get_admin_config()
    
    # Verify current password
    if not admin.verify_admin_password(password_data.current_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Change password
    if admin.change_admin_password(password_data.new_password):
        logger.info("Admin password changed")
        return {"success": True, "message": "Password changed successfully"}
    
    raise HTTPException(status_code=500, detail="Failed to change password")


@router.get("/usage")
async def get_usage(request: Request):
    """Get usage statistics. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    admin = get_admin_config()
    
    return {
        "today": admin.get_today_usage(),
        "month": admin.get_month_usage(),
        "history": admin.get_usage_history(30),
        "limits": {
            "daily": admin.get_config_int('daily_token_limit', 100000),
            "monthly": admin.get_config_int('monthly_token_limit', 2000000),
        },
        "rate_limit_check": admin.check_rate_limit()
    }


@router.get("/rate-check")
async def check_rate_limit():
    """
    Public endpoint to check if rate limits are exceeded.
    Used by frontend to show warnings.
    """
    admin = get_admin_config()
    return admin.check_rate_limit()


# ==================== Prompt Management ====================

@router.get("/prompts")
async def get_prompts(request: Request):
    """Get all prompts. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    prompt_manager = get_prompt_manager()
    return {
        "prompts": prompt_manager.get_all_prompts()
    }


@router.get("/prompts/{key}")
async def get_prompt(key: str, request: Request):
    """Get a specific prompt by key. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Sanitize key input
    if not key.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="Invalid prompt key")
    
    prompt_manager = get_prompt_manager()
    prompt = prompt_manager.get_prompt_full(key)
    
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    return prompt


@router.post("/prompts")
async def update_prompt(request: Request, prompt_data: PromptUpdateRequest):
    """Update a prompt. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    prompt_manager = get_prompt_manager()
    success = prompt_manager.update_prompt(prompt_data.key, prompt_data.content, "admin")
    
    if success:
        logger.info(f"Admin updated prompt: {prompt_data.key}")
        return {"success": True, "message": f"Prompt updated"}
    
    raise HTTPException(status_code=500, detail="Failed to update prompt")


@router.post("/prompts/{key}/reset")
async def reset_prompt(key: str, request: Request):
    """Reset a prompt to default. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Sanitize key input
    if not key.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="Invalid prompt key")
    
    prompt_manager = get_prompt_manager()
    success = prompt_manager.reset_prompt(key)
    
    if success:
        logger.info(f"Admin reset prompt to default: {key}")
        return {"success": True, "message": "Prompt reset to default"}
    
    raise HTTPException(status_code=500, detail="Failed to reset prompt")


@router.get("/prompts/{key}/history")
async def get_prompt_history(key: str, request: Request, limit: int = 10):
    """Get version history for a prompt. Requires admin cookie."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Sanitize inputs
    if not key.replace('_', '').replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail="Invalid prompt key")
    limit = min(max(1, limit), 100)  # Clamp between 1-100
    
    prompt_manager = get_prompt_manager()
    return {
        "history": prompt_manager.get_prompt_history(key, limit)
    }


# ==================== Admin UI ====================

@router.get("/ui", response_class=HTMLResponse)
async def admin_ui():
    """Admin panel UI."""
    return get_admin_html()


def get_admin_html() -> str:
    """Return the admin panel HTML with prompts management."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Admin Panel - Arctic Debate Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --bg-dark: #0f1419;
            --bg-card: #1a1f2e;
            --bg-input: #252b3b;
            --accent-blue: #00d9ff;
            --accent-green: #00ff88;
            --accent-red: #ff6b6b;
            --accent-yellow: #ffd93d;
            --accent-purple: #a855f7;
            --text-primary: #e8e8e8;
            --text-secondary: #888;
            --border: rgba(255,255,255,0.1);
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #16213e 100%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 20px;
        }
        
        .container { max-width: 1100px; margin: 0 auto; }
        
        h1 {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 20px;
            background: linear-gradient(135deg, var(--accent-red), var(--accent-yellow));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .tabs {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }
        
        .tab-btn {
            padding: 10px 20px;
            border: 1px solid var(--border);
            border-radius: 8px 8px 0 0;
            background: var(--bg-input);
            color: var(--text-secondary);
            cursor: pointer;
            font-size: 0.95rem;
            transition: all 0.2s;
        }
        
        .tab-btn.active {
            background: var(--bg-card);
            color: var(--accent-blue);
            border-bottom-color: var(--bg-card);
        }
        
        .tab-btn:hover { color: var(--text-primary); }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        input, select, textarea {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--bg-input);
            color: var(--text-primary);
            font-size: 1rem;
            margin-bottom: 12px;
            font-family: inherit;
        }
        
        textarea {
            min-height: 200px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            line-height: 1.5;
            resize: vertical;
        }
        
        input:focus, textarea:focus { outline: none; border-color: var(--accent-blue); }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 600;
            transition: all 0.2s;
            margin-right: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
            color: var(--bg-dark);
        }
        
        .btn-secondary {
            background: var(--bg-input);
            color: var(--text-primary);
            border: 1px solid var(--border);
        }
        
        .btn-danger {
            background: var(--accent-red);
            color: white;
        }
        
        .btn-purple {
            background: linear-gradient(135deg, var(--accent-purple), #ec4899);
            color: white;
        }
        
        .btn:hover { transform: translateY(-2px); opacity: 0.9; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        .login-container {
            max-width: 400px;
            margin: 100px auto;
        }
        
        .hidden { display: none !important; }
        
        .config-row {
            display: grid;
            grid-template-columns: 1fr 150px;
            gap: 12px;
            align-items: center;
            padding: 12px;
            background: var(--bg-input);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        
        .config-key {
            font-weight: 500;
            color: var(--accent-blue);
        }
        
        .usage-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }
        
        .stat-box {
            background: var(--bg-input);
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: var(--accent-green);
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }
        
        .warning { color: var(--accent-yellow); }
        .danger { color: var(--accent-red); }
        .success { color: var(--accent-green); }
        
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            border-radius: 8px;
            background: var(--bg-card);
            border: 1px solid var(--accent-green);
            color: var(--accent-green);
            z-index: 1000;
        }
        
        .back-link {
            display: inline-block;
            margin-bottom: 20px;
            color: var(--accent-blue);
            text-decoration: none;
        }
        
        .back-link:hover { text-decoration: underline; }
        
        .prompt-card {
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .prompt-card:hover {
            border-color: var(--accent-blue);
            transform: translateX(4px);
        }
        
        .prompt-card.active {
            border-color: var(--accent-purple);
            background: rgba(168, 85, 247, 0.1);
        }
        
        .prompt-name {
            font-weight: 600;
            color: var(--accent-purple);
            margin-bottom: 4px;
        }
        
        .prompt-category {
            display: inline-block;
            font-size: 0.75rem;
            padding: 2px 8px;
            background: var(--bg-dark);
            border-radius: 4px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }
        
        .prompt-desc {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .prompt-editor {
            display: none;
        }
        
        .prompt-editor.active {
            display: block;
        }
        
        .prompt-grid {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 20px;
        }
        
        @media (max-width: 768px) {
            .prompt-grid {
                grid-template-columns: 1fr;
            }
        }
        
        .char-count {
            text-align: right;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: -8px;
            margin-bottom: 12px;
        }
        
        .variable-list {
            background: var(--bg-dark);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
        }
        
        .variable-list h4 {
            font-size: 0.9rem;
            color: var(--accent-yellow);
            margin-bottom: 8px;
        }
        
        .variable-tag {
            display: inline-block;
            background: var(--bg-input);
            padding: 2px 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.8rem;
            margin: 2px;
            color: var(--accent-blue);
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/ui" class="back-link">← Back to Main App</a>
        <h1>🔐 Admin Panel</h1>
        
        <!-- Login Form -->
        <div id="loginSection" class="login-container">
            <div class="card">
                <div class="card-title">🔑 Admin Login</div>
                <input type="password" id="loginPassword" placeholder="Enter admin password" onkeypress="if(event.key==='Enter')login()">
                <button class="btn btn-primary" onclick="login()" style="width: 100%;">Login</button>
                <p id="loginError" class="danger" style="margin-top: 12px; display: none;"></p>
            </div>
        </div>
        
        <!-- Admin Dashboard (hidden until login) -->
        <div id="dashboardSection" class="hidden">
            <!-- Tabs -->
            <div class="tabs">
                <button class="tab-btn active" onclick="showAdminTab('usage')">📊 Usage</button>
                <button class="tab-btn" onclick="showAdminTab('config')">⚙️ Config</button>
                <button class="tab-btn" onclick="showAdminTab('prompts')">📝 Prompts</button>
                <button class="tab-btn" onclick="showAdminTab('security')">🔒 Security</button>
            </div>
            
            <!-- Usage Tab -->
            <div id="tab-usage" class="tab-content active">
                <div class="card">
                    <div class="card-title">📊 Usage Statistics</div>
                    <div class="usage-stats" id="usageStats">
                        <div class="stat-box">
                            <div class="stat-value" id="todayTokens">-</div>
                            <div class="stat-label">Tokens Today</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="todayRequests">-</div>
                            <div class="stat-label">Requests Today</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="monthTokens">-</div>
                            <div class="stat-label">Tokens This Month</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="dailyRemaining">-</div>
                            <div class="stat-label">Daily Remaining</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Config Tab -->
            <div id="tab-config" class="tab-content">
                <div class="card">
                    <div class="card-title">⚙️ Rate Limits & Configuration</div>
                    <div id="configList"></div>
                    <button class="btn btn-primary" onclick="saveAllConfig()" style="margin-top: 16px;">💾 Save All Changes</button>
                </div>
            </div>
            
            <!-- Prompts Tab -->
            <div id="tab-prompts" class="tab-content">
                <div class="card">
                    <div class="card-title">📝 AI Prompt Templates</div>
                    <p style="color: var(--text-secondary); margin-bottom: 16px;">
                        Customize the prompts used for article analysis, card generation, and chat. 
                        Changes take effect immediately.
                    </p>
                    
                    <div class="prompt-grid">
                        <!-- Prompt List -->
                        <div id="promptList">
                            <p style="color: var(--text-secondary);">Loading prompts...</p>
                        </div>
                        
                        <!-- Prompt Editor -->
                        <div id="promptEditor" class="prompt-editor">
                            <div class="card" style="margin-bottom: 0;">
                                <div class="card-title">
                                    <span id="editingPromptName">Select a prompt</span>
                                </div>
                                
                                <div class="variable-list" id="variableList" style="display: none;">
                                    <h4>📌 Available Variables</h4>
                                    <div id="variableTags"></div>
                                </div>
                                
                                <textarea id="promptContent" placeholder="Select a prompt from the list to edit..."></textarea>
                                <div class="char-count"><span id="charCount">0</span> characters</div>
                                
                                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                                    <button class="btn btn-primary" onclick="savePrompt()" id="savePromptBtn" disabled>💾 Save Changes</button>
                                    <button class="btn btn-secondary" onclick="resetPrompt()" id="resetPromptBtn" disabled>🔄 Reset to Default</button>
                                    <button class="btn btn-purple" onclick="previewPrompt()" id="previewPromptBtn" disabled>👁️ Preview</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Security Tab -->
            <div id="tab-security" class="tab-content">
                <div class="card">
                    <div class="card-title">🔒 Change Admin Password</div>
                    <input type="password" id="currentPassword" placeholder="Current password">
                    <input type="password" id="newPassword" placeholder="New password">
                    <input type="password" id="confirmPassword" placeholder="Confirm new password">
                    <button class="btn btn-danger" onclick="changePassword()">Change Password</button>
                </div>
                
                <div class="card" style="text-align: center;">
                    <button class="btn btn-danger" onclick="logout()">🚪 Logout</button>
                </div>
            </div>
        </div>
    </div>
    
    <div id="toast" class="toast hidden"></div>
    
    <script>
        // SECURITY: Using HttpOnly cookies - no token in localStorage
        let configChanges = {};
        let currentPromptKey = null;
        let prompts = [];
        
        // Check if already logged in (cookie-based)
        checkSession();
        
        function showAdminTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            // Show selected tab
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load data if needed
            if (tabName === 'prompts') loadPrompts();
        }
        
        async function checkSession() {
            try {
                // Credentials:'include' sends cookies automatically
                const res = await fetch('/admin/usage', {credentials: 'include'});
                if (res.ok) {
                    showDashboard();
                    loadUsage();
                    loadConfig();
                }
            } catch (e) {
                console.log('Not authenticated');
            }
        }
        
        async function login() {
            const password = document.getElementById('loginPassword').value;
            const errorEl = document.getElementById('loginError');
            
            try {
                const res = await fetch('/admin/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',  // For cookie
                    body: JSON.stringify({password})
                });
                
                if (res.ok) {
                    showDashboard();
                    loadUsage();
                    loadConfig();
                    showToast('Login successful!');
                } else {
                    const data = await res.json();
                    errorEl.textContent = data.detail || 'Invalid password';
                    errorEl.style.display = 'block';
                }
            } catch (e) {
                errorEl.textContent = 'Connection error';
                errorEl.style.display = 'block';
            }
        }
        
        function showDashboard() {
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('dashboardSection').classList.remove('hidden');
        }
        
        async function loadUsage() {
            try {
                const res = await fetch('/admin/usage', {credentials: 'include'});
                const data = await res.json();
                
                document.getElementById('todayTokens').textContent = (data.today.total_tokens || 0).toLocaleString();
                document.getElementById('todayRequests').textContent = data.today.total_requests || 0;
                document.getElementById('monthTokens').textContent = (data.month.total_tokens || 0).toLocaleString();
                
                const remaining = data.rate_limit_check.daily_remaining;
                const remainingEl = document.getElementById('dailyRemaining');
                remainingEl.textContent = remaining ? remaining.toLocaleString() : '0';
                
                if (remaining < 10000) {
                    remainingEl.classList.add('danger');
                } else if (remaining < 30000) {
                    remainingEl.classList.add('warning');
                }
                
            } catch (e) {
                console.error('Failed to load usage:', e);
            }
        }
        
        async function loadConfig() {
            try {
                const res = await fetch('/admin/config', {credentials: 'include'});
                const data = await res.json();
                
                const container = document.getElementById('configList');
                container.innerHTML = '';
                
                const configItems = [
                    {key: 'daily_token_limit', label: 'Daily Token Limit', type: 'number'},
                    {key: 'monthly_token_limit', label: 'Monthly Token Limit', type: 'number'},
                    {key: 'max_requests_per_minute', label: 'Max Requests/Minute', type: 'number'},
                    {key: 'max_tokens_per_request', label: 'Max Tokens/Request', type: 'number'},
                    {key: 'enable_rate_limiting', label: 'Enable Rate Limiting', type: 'boolean'},
                    {key: 'enable_usage_tracking', label: 'Enable Usage Tracking', type: 'boolean'},
                ];
                
                for (const item of configItems) {
                    const configData = data.config[item.key];
                    const value = configData ? configData.value : data.defaults[item.key];
                    
                    const row = document.createElement('div');
                    row.className = 'config-row';
                    
                    if (item.type === 'boolean') {
                        row.innerHTML = `
                            <div class="config-key">${item.label}</div>
                            <select id="config_${item.key}" onchange="markChanged('${item.key}')">
                                <option value="true" ${value === 'True' || value === 'true' || value === true ? 'selected' : ''}>Enabled</option>
                                <option value="false" ${value === 'False' || value === 'false' || value === false ? 'selected' : ''}>Disabled</option>
                            </select>
                        `;
                    } else {
                        row.innerHTML = `
                            <div class="config-key">${item.label}</div>
                            <input type="number" id="config_${item.key}" value="${value}" onchange="markChanged('${item.key}')">
                        `;
                    }
                    
                    container.appendChild(row);
                }
                
            } catch (e) {
                console.error('Failed to load config:', e);
            }
        }
        
        // ==================== PROMPTS ====================
        
        async function loadPrompts() {
            try {
                const res = await fetch('/admin/prompts', {credentials: 'include'});
                const data = await res.json();
                prompts = data.prompts;
                
                const container = document.getElementById('promptList');
                container.innerHTML = '';
                
                // Group by category
                const categories = {};
                for (const p of prompts) {
                    const cat = p.category || 'general';
                    if (!categories[cat]) categories[cat] = [];
                    categories[cat].push(p);
                }
                
                for (const [category, items] of Object.entries(categories)) {
                    const catLabel = document.createElement('div');
                    catLabel.style.cssText = 'font-size: 0.8rem; color: var(--text-secondary); text-transform: uppercase; margin: 16px 0 8px; letter-spacing: 1px;';
                    catLabel.textContent = category;
                    container.appendChild(catLabel);
                    
                    for (const p of items) {
                        const card = document.createElement('div');
                        card.className = 'prompt-card';
                        card.id = 'prompt-card-' + p.key;
                        card.onclick = () => selectPrompt(p.key);
                        card.innerHTML = `
                            <div class="prompt-name">${p.name}</div>
                            <div class="prompt-desc">${p.description || 'No description'}</div>
                        `;
                        container.appendChild(card);
                    }
                }
                
                // Show editor
                document.getElementById('promptEditor').classList.add('active');
                
            } catch (e) {
                console.error('Failed to load prompts:', e);
                document.getElementById('promptList').innerHTML = '<p class="danger">Failed to load prompts</p>';
            }
        }
        
        function selectPrompt(key) {
            currentPromptKey = key;
            const prompt = prompts.find(p => p.key === key);
            if (!prompt) return;
            
            // Update selection UI
            document.querySelectorAll('.prompt-card').forEach(el => el.classList.remove('active'));
            document.getElementById('prompt-card-' + key).classList.add('active');
            
            // Fill editor
            document.getElementById('editingPromptName').textContent = prompt.name;
            document.getElementById('promptContent').value = prompt.content;
            document.getElementById('charCount').textContent = prompt.content.length;
            
            // Show variables based on prompt type
            const variableList = document.getElementById('variableList');
            const variableTags = document.getElementById('variableTags');
            
            const variables = {
                'article_analysis': ['{topic_context}', '{title}', '{source}', '{text}'],
                'topic_context': [],
                'card_tag_generation': ['{context}', '{evidence}'],
                'card_highlighting': ['{evidence}'],
                'chat_system': []
            };
            
            const vars = variables[key] || [];
            if (vars.length > 0) {
                variableList.style.display = 'block';
                variableTags.innerHTML = vars.map(v => `<span class="variable-tag">${v}</span>`).join('');
            } else {
                variableList.style.display = 'none';
            }
            
            // Enable buttons
            document.getElementById('savePromptBtn').disabled = false;
            document.getElementById('resetPromptBtn').disabled = false;
            document.getElementById('previewPromptBtn').disabled = false;
        }
        
        async function savePrompt() {
            if (!currentPromptKey) return;
            
            const content = document.getElementById('promptContent').value;
            
            try {
                const res = await fetch('/admin/prompts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({key: currentPromptKey, content})
                });
                
                if (res.ok) {
                    showToast('Prompt saved successfully!');
                    // Update local data
                    const idx = prompts.findIndex(p => p.key === currentPromptKey);
                    if (idx >= 0) prompts[idx].content = content;
                } else {
                    showToast('Failed to save prompt', 'error');
                }
            } catch (e) {
                showToast('Error saving prompt', 'error');
            }
        }
        
        async function resetPrompt() {
            if (!currentPromptKey) return;
            if (!confirm('Reset this prompt to its default value?')) return;
            
            try {
                const res = await fetch('/admin/prompts/' + currentPromptKey + '/reset', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (res.ok) {
                    showToast('Prompt reset to default');
                    loadPrompts();
                    setTimeout(() => selectPrompt(currentPromptKey), 300);
                } else {
                    showToast('Failed to reset prompt', 'error');
                }
            } catch (e) {
                showToast('Error resetting prompt', 'error');
            }
        }
        
        function previewPrompt() {
            const content = document.getElementById('promptContent').value;
            
            // Simple preview - replace variables with sample values
            let preview = content
                .replace('{topic_context}', '[TOPIC CONTEXT INSERTED HERE]')
                .replace('{title}', 'Sample Article Title')
                .replace('{source}', 'Example Source')
                .replace('{text}', '[ARTICLE TEXT CONTENT...]')
                .replace('{evidence}', '[EVIDENCE TEXT...]')
                .replace('{context}', 'Arctic cod protection affirmative');
            
            alert('PROMPT PREVIEW:\\n\\n' + preview.substring(0, 1500) + (preview.length > 1500 ? '...' : ''));
        }
        
        // Update character count on input
        document.getElementById('promptContent').addEventListener('input', function() {
            document.getElementById('charCount').textContent = this.value.length;
        });
        
        function markChanged(key) {
            const el = document.getElementById('config_' + key);
            configChanges[key] = el.value;
        }
        
        async function saveAllConfig() {
            const keys = Object.keys(configChanges);
            if (keys.length === 0) {
                showToast('No changes to save');
                return;
            }
            
            let saved = 0;
            for (const key of keys) {
                try {
                    await fetch('/admin/config', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        credentials: 'include',
                        body: JSON.stringify({key, value: configChanges[key]})
                    });
                    saved++;
                } catch (e) {
                    console.error('Failed to save:', key);
                }
            }
            
            configChanges = {};
            showToast(`Saved ${saved} configuration(s)`);
            loadUsage();
        }
        
        async function changePassword() {
            const current = document.getElementById('currentPassword').value;
            const newPass = document.getElementById('newPassword').value;
            const confirm = document.getElementById('confirmPassword').value;
            
            if (!current || !newPass) {
                showToast('Please fill all fields', 'error');
                return;
            }
            
            if (newPass !== confirm) {
                showToast('New passwords do not match', 'error');
                return;
            }
            
            if (newPass.length < 8) {
                showToast('Password must be at least 8 characters', 'error');
                return;
            }
            
            try {
                const res = await fetch('/admin/change-password', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include',
                    body: JSON.stringify({current_password: current, new_password: newPass})
                });
                
                if (res.ok) {
                    showToast('Password changed successfully!');
                    document.getElementById('currentPassword').value = '';
                    document.getElementById('newPassword').value = '';
                    document.getElementById('confirmPassword').value = '';
                } else {
                    const data = await res.json();
                    showToast(data.detail || 'Failed to change password', 'error');
                }
            } catch (e) {
                showToast('Error changing password', 'error');
            }
        }
        
        async function logout() {
            await fetch('/admin/logout', {method: 'POST', credentials: 'include'});
            location.reload();
        }
        
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.borderColor = type === 'error' ? 'var(--accent-red)' : 'var(--accent-green)';
            toast.style.color = type === 'error' ? 'var(--accent-red)' : 'var(--accent-green)';
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 3000);
        }
    </script>
</body>
</html>'''

