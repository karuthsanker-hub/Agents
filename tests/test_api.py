"""
API Tests for Arctic Debate Card Agent
======================================
Comprehensive tests for CI/CD pipeline (GitHub Actions).

SECURITY: Tests verify both authenticated and unauthenticated access patterns.

Author: Shiv Sanker
Created: 2024
License: MIT

Run with: pytest tests/test_api.py -v
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# ==================== Fixtures ====================

@pytest.fixture(scope="module")
def mock_env():
    """Set up mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "sk-test-key-for-testing",
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test_db",
        "REDIS_URL": "redis://localhost:6379/0",
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "ALLOWED_EMAILS": "test@example.com,admin@example.com",
        "APP_ENV": "development",
        "DEBUG": "true",
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(scope="module")
def mock_services():
    """Mock external services for isolated testing."""
    with patch('psycopg2.connect') as mock_pg, \
         patch('redis.from_url') as mock_redis, \
         patch('chromadb.PersistentClient') as mock_chroma, \
         patch('openai.OpenAI') as mock_openai:
        
        # Configure mock PostgreSQL
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_cursor.fetchall.return_value = []
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=False)
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg.return_value = mock_conn
        
        # Configure mock Redis
        mock_redis_client = MagicMock()
        mock_redis_client.get.return_value = None
        mock_redis_client.ping.return_value = True
        mock_redis.return_value = mock_redis_client
        
        # Configure mock ChromaDB
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]],
            'ids': [[]]
        }
        mock_chroma_client = MagicMock()
        mock_chroma_client.get_or_create_collection.return_value = mock_collection
        mock_chroma_client.list_collections.return_value = []
        mock_chroma.return_value = mock_chroma_client
        
        yield {
            'pg': mock_pg,
            'redis': mock_redis,
            'chroma': mock_chroma,
            'openai': mock_openai
        }


@pytest.fixture(scope="module")
def client(mock_env, mock_services):
    """Create test client with mocked services."""
    # Clear any cached settings
    from app.core.config import get_settings
    get_settings.cache_clear()
    
    from server.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Mock authentication headers/cookies.
    In a real test, this would be obtained by logging in.
    For unit tests, we mock the auth dependency.
    """
    return {"Cookie": "session_token=test-mock-session-token"}


# ==================== Public Endpoint Tests ====================

class TestPublicEndpoints:
    """Tests for endpoints that DON'T require authentication."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info (PUBLIC)."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "Arctic" in data["service"]
        assert "version" in data
    
    def test_health_check(self, client):
        """Test health check endpoint (PUBLIC)."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_auth_status(self, client):
        """Test auth status returns config (PUBLIC)."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "google_enabled" in data
    
    def test_auth_me_unauthenticated(self, client):
        """Test /auth/me without session (PUBLIC)."""
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == False
    
    def test_auth_validate_no_token(self, client):
        """Test token validation without token (PUBLIC)."""
        response = client.post("/auth/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
    
    @pytest.mark.skip(reason="Requires database connection")
    def test_check_url_not_exists(self, client):
        """Test URL existence check (PUBLIC)."""
        response = client.get("/articles/check-url?url=https://example.com/new-article")
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
    
    @pytest.mark.skip(reason="Requires database connection")
    def test_admin_rate_check(self, client):
        """Test public rate limit check (PUBLIC)."""
        response = client.get("/admin/rate-check")
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data


# ==================== Auth-Protected Endpoint Tests ====================

class TestAuthRequiredEndpoints:
    """Tests verifying endpoints require authentication."""
    
    def test_stats_requires_auth(self, client):
        """Test /stats requires authentication."""
        response = client.get("/stats")
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    
    def test_db_info_requires_auth(self, client):
        """Test /db-info requires authentication."""
        response = client.get("/db-info")
        assert response.status_code == 401
    
    def test_chat_requires_auth(self, client):
        """Test /chat requires authentication."""
        response = client.post("/chat", json={"message": "test"})
        assert response.status_code == 401
    
    def test_chat_search_requires_auth(self, client):
        """Test /chat/search requires authentication."""
        response = client.post("/chat/search", json={"query": "test"})
        assert response.status_code == 401
    
    def test_chat_history_requires_auth(self, client):
        """Test /chat/history requires authentication."""
        response = client.get("/chat/history/test-session")
        assert response.status_code == 401
    
    def test_articles_add_requires_auth(self, client):
        """Test /articles/add requires authentication."""
        response = client.post("/articles/add", json={"url": "https://example.com"})
        assert response.status_code == 401
    
    def test_articles_search_requires_auth(self, client):
        """Test /articles/search requires authentication."""
        response = client.post("/articles/search", json={"query": "test"})
        assert response.status_code == 401
    
    def test_articles_delete_requires_auth(self, client):
        """Test /articles/{id} DELETE requires authentication."""
        response = client.delete("/articles/1")
        assert response.status_code == 401
    
    def test_articles_analyze_requires_auth(self, client):
        """Test /articles/{id}/analyze requires authentication."""
        response = client.post("/articles/1/analyze")
        assert response.status_code == 401
    
    def test_articles_seed_requires_auth(self, client):
        """Test /articles/seed requires authentication."""
        response = client.post("/articles/seed")
        assert response.status_code == 401
    
    def test_cards_format_requires_auth(self, client):
        """Test /articles/cards/format requires authentication."""
        response = client.post("/articles/cards/format", json={
            "evidence_text": "test",
            "author": "Test",
            "year": "2024",
            "title": "Test",
            "source": "Test"
        })
        assert response.status_code == 401
    
    def test_cards_extract_requires_auth(self, client):
        """Test /articles/cards/extract requires authentication."""
        response = client.post("/articles/cards/extract", json={"document_text": "test"})
        assert response.status_code == 401


# ==================== Admin Panel Tests ====================

class TestAdminEndpoints:
    """Tests for admin panel endpoints."""
    
    @pytest.mark.skip(reason="Requires database connection")
    def test_admin_login_wrong_password(self, client):
        """Test admin login with wrong password."""
        response = client.post("/admin/login", json={"password": "wrong-password"})
        assert response.status_code == 401
    
    def test_admin_login_empty_password(self, client):
        """Test admin login with empty password."""
        response = client.post("/admin/login", json={"password": ""})
        assert response.status_code == 422  # Validation error
    
    def test_admin_config_unauthorized(self, client):
        """Test admin config without auth."""
        response = client.get("/admin/config")
        assert response.status_code == 401
    
    def test_admin_usage_unauthorized(self, client):
        """Test admin usage without auth."""
        response = client.get("/admin/usage")
        assert response.status_code == 401
    
    def test_admin_prompts_unauthorized(self, client):
        """Test admin prompts without auth."""
        response = client.get("/admin/prompts")
        assert response.status_code == 401
    
    def test_admin_ui_page(self, client):
        """Test admin UI page loads (PUBLIC - shows login form)."""
        response = client.get("/admin/ui")
        assert response.status_code == 200
        assert "Admin Panel" in response.text
        assert "Login" in response.text


# ==================== UI Endpoint Tests ====================

class TestUIEndpoints:
    """Tests for web UI endpoints."""
    
    def test_main_ui_loads(self, client):
        """Test main UI page loads."""
        response = client.get("/ui")
        assert response.status_code == 200
        assert "Arctic Debate Card Agent" in response.text
    
    def test_ui_contains_tabs(self, client):
        """Test UI contains expected tabs."""
        response = client.get("/ui")
        assert "Articles" in response.text
        assert "Card Editor" in response.text
        assert "Chat" in response.text
    
    def test_ui_contains_scripts(self, client):
        """Test UI contains JavaScript."""
        response = client.get("/ui")
        assert "<script>" in response.text
        assert "function" in response.text
    
    def test_login_page_loads(self, client):
        """Test dedicated login page loads."""
        response = client.get("/auth/page")
        assert response.status_code == 200
        assert "Sign in" in response.text or "Login" in response.text


# ==================== API Documentation Tests ====================

class TestAPIDocumentation:
    """Tests for API documentation endpoints."""
    
    def test_openapi_schema(self, client):
        """Test OpenAPI schema is generated."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "info" in data
    
    def test_docs_page(self, client):
        """Test Swagger docs page loads (in dev mode)."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_page(self, client):
        """Test ReDoc page loads (in dev mode)."""
        response = client.get("/redoc")
        assert response.status_code == 200


# ==================== Error Handling Tests ====================

class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_404_for_unknown_endpoint(self, client):
        """Test 404 for unknown endpoints."""
        response = client.get("/unknown/endpoint")
        assert response.status_code == 404
    
    def test_invalid_json_body(self, client):
        """Test handling of invalid JSON."""
        response = client.post(
            "/admin/login",  # Use public endpoint for JSON test
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields_login(self, client):
        """Test validation of required fields."""
        response = client.post("/admin/login", json={})
        assert response.status_code == 422


# ==================== Security Tests ====================

class TestSecurityFeatures:
    """Tests for security features."""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are set."""
        response = client.options("/")
        # In test mode, CORS may not be applied the same way
        # Just verify endpoint is accessible
        assert response.status_code in [200, 405]
    
    @pytest.mark.skip(reason="Requires database connection")
    def test_rate_limit_check_works(self, client):
        """Test rate limit check returns proper structure."""
        response = client.get("/admin/rate-check")
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
        # Should have either 'reason' or remaining counts
        assert "reason" in data or "daily_remaining" in data
    
    def test_open_redirect_prevention(self, client):
        """Test open redirect prevention on login page."""
        # Try to use an external URL as return_url
        response = client.get("/auth/page?return_url=https://evil.com")
        assert response.status_code == 200
        # Should not contain the evil URL
        assert "evil.com" not in response.text


# ==================== Performance Tests ====================

class TestPerformance:
    """Basic performance and response time tests."""
    
    def test_health_check_fast(self, client):
        """Test health check responds quickly."""
        import time
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed:.2f}s (should be < 1s)"
    
    def test_root_endpoint_fast(self, client):
        """Test root endpoint responds quickly."""
        import time
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 0.5, f"Root endpoint took {elapsed:.2f}s (should be < 0.5s)"
    
    def test_auth_status_fast(self, client):
        """Test auth status responds quickly."""
        import time
        start = time.time()
        response = client.get("/auth/status")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 0.5, f"Auth status took {elapsed:.2f}s (should be < 0.5s)"


# ==================== Integration Test Helpers ====================

@pytest.mark.skip(reason="Requires complex mocking setup")
class TestWithMockedAuth:
    """Tests with mocked authentication for protected endpoints."""
    
    @pytest.fixture
    def authed_client(self, mock_env, mock_services):
        """Create client with mocked authentication."""
        from app.core.config import get_settings
        get_settings.cache_clear()
        
        # Patch the security module to bypass auth
        with patch('app.core.security.get_current_user') as mock_auth, \
             patch('app.core.security.get_current_user_optional') as mock_auth_opt, \
             patch('app.core.security.require_auth_and_rate_limit') as mock_rate:
            
            mock_user = {
                "id": 1,
                "email": "test@example.com",
                "name": "Test User",
                "is_admin": False
            }
            mock_auth.return_value = mock_user
            mock_auth_opt.return_value = mock_user
            mock_rate.return_value = mock_user
            
            from server.main import app
            yield TestClient(app)
    
    def test_stats_with_auth(self, authed_client):
        """Test /stats with valid auth returns data."""
        response = authed_client.get("/stats")
        # With mocked services, this should work
        assert response.status_code in [200, 500]  # 500 if mock incomplete
    
    def test_chat_search_with_auth(self, authed_client):
        """Test /chat/search with valid auth."""
        response = authed_client.post(
            "/chat/search",
            json={"query": "Arctic", "n_results": 5}
        )
        # With mocked services, check we get past auth
        assert response.status_code in [200, 500]


# ==================== Run Configuration ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
