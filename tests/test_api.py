"""
API Tests for Arctic Debate Card Agent
======================================
Comprehensive tests for CI/CD pipeline (GitHub Actions).

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
        mock_cursor.fetchone.return_value = {'count': 0}
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


# ==================== System Endpoint Tests ====================

class TestSystemEndpoints:
    """Tests for system health and info endpoints."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "Arctic" in data["service"]
        assert "version" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "services" in data
    
    def test_stats_endpoint(self, client):
        """Test statistics endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "agent_stats" in data or "error" in data
    
    def test_db_info_endpoint(self, client):
        """Test database info endpoint."""
        response = client.get("/db-info")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ==================== Auth Endpoint Tests ====================

class TestAuthEndpoints:
    """Tests for authentication endpoints."""
    
    def test_auth_status(self, client):
        """Test auth status returns config."""
        response = client.get("/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "google_enabled" in data
    
    def test_auth_me_unauthenticated(self, client):
        """Test /auth/me without session."""
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] == False
    
    def test_auth_validate_no_token(self, client):
        """Test token validation without token."""
        response = client.post("/auth/validate")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False


# ==================== Articles Endpoint Tests ====================

class TestArticlesEndpoints:
    """Tests for article management endpoints."""
    
    def test_list_articles_empty(self, client):
        """Test listing articles when empty."""
        response = client.get("/articles")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert "total" in data
        assert isinstance(data["articles"], list)
    
    def test_list_articles_with_filters(self, client):
        """Test listing articles with filters."""
        response = client.get("/articles?side=aff&limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert data["limit"] == 10
        assert data["offset"] == 0
    
    def test_list_articles_pagination(self, client):
        """Test pagination parameters."""
        response = client.get("/articles?limit=5&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 10
        assert "has_more" in data
    
    def test_check_url_not_exists(self, client):
        """Test URL existence check for new URL."""
        response = client.get("/articles/check-url?url=https://example.com/new-article")
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
    
    def test_search_articles(self, client):
        """Test semantic article search."""
        response = client.post(
            "/articles/search",
            json={"query": "Arctic climate change", "n_results": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "articles" in data
        assert isinstance(data["articles"], list)
    
    def test_get_nonexistent_article(self, client):
        """Test getting article that doesn't exist."""
        response = client.get("/articles/99999")
        assert response.status_code == 404


# ==================== Admin Endpoint Tests ====================

class TestAdminEndpoints:
    """Tests for admin panel endpoints."""
    
    def test_admin_rate_check(self, client):
        """Test public rate limit check."""
        response = client.get("/admin/rate-check")
        assert response.status_code == 200
        data = response.json()
        assert "allowed" in data
    
    def test_admin_login_wrong_password(self, client):
        """Test admin login with wrong password."""
        response = client.post(
            "/admin/login",
            json={"password": "wrong-password"}
        )
        assert response.status_code == 401
    
    def test_admin_config_unauthorized(self, client):
        """Test admin config without auth."""
        response = client.get("/admin/config?token=invalid-token")
        assert response.status_code == 401
    
    def test_admin_usage_unauthorized(self, client):
        """Test admin usage without auth."""
        response = client.get("/admin/usage?token=invalid-token")
        assert response.status_code == 401
    
    def test_admin_ui_page(self, client):
        """Test admin UI page loads."""
        response = client.get("/admin/ui")
        assert response.status_code == 200
        assert "Admin Panel" in response.text


# ==================== Chat Endpoint Tests ====================

class TestChatEndpoints:
    """Tests for chat/research assistant endpoints."""
    
    def test_chat_search_empty(self, client):
        """Test chat search with no history."""
        response = client.post(
            "/chat/search",
            json={"query": "Arctic", "n_results": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "memories" in data
    
    def test_chat_history_empty(self, client):
        """Test getting empty chat history."""
        response = client.get("/chat/history/test-session-123")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data


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
        """Test Swagger docs page loads."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_page(self, client):
        """Test ReDoc page loads."""
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
            "/chat",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test validation of required fields."""
        response = client.post(
            "/articles/add",
            json={}  # Missing required 'url' field
        )
        assert response.status_code == 422


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


# ==================== Run Configuration ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
