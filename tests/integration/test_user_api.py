"""Integration tests for User API.

Tests the full flow: HTTP → Controller → Action → Repository → Database.
Uses Litestar TestClient with real database (SQLite in-memory or test file).
"""

import pytest
from uuid import UUID

from litestar.testing import TestClient

from src.App import create_app


@pytest.fixture(scope="module")
def client():
    """Create test client with real app."""
    app = create_app()
    with TestClient(app=app) as client:
        yield client


@pytest.fixture
def unique_email():
    """Generate unique email for each test."""
    import uuid
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


class TestUserCreation:
    """Tests for user creation flow."""
    
    def test_create_user_success(self, client: TestClient, unique_email: str) -> None:
        """Test successful user creation via API."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "secure_password_123",
                "name": "Test User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == unique_email
        assert data["name"] == "Test User"
        assert data["is_active"] is True
        assert "id" in data
        # Password should NOT be in response
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_create_user_duplicate_email(self, client: TestClient, unique_email: str) -> None:
        """Test that duplicate email returns 409 Conflict."""
        # Create first user
        client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "First User",
            },
        )
        
        # Try to create second user with same email
        response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password456",
                "name": "Second User",
            },
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "USER_ALREADY_EXISTS"
    
    def test_create_user_invalid_email(self, client: TestClient) -> None:
        """Test that invalid email returns validation error (400 in Litestar)."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "not-an-email",
                "password": "password123",
                "name": "Test User",
            },
        )
        
        # Litestar returns 400 for validation errors by default
        assert response.status_code in [400, 422]
    
    def test_create_user_short_password(self, client: TestClient, unique_email: str) -> None:
        """Test that short password returns validation error (400 in Litestar)."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "short",  # Less than 8 chars
                "name": "Test User",
            },
        )
        
        # Litestar returns 400 for validation errors by default
        assert response.status_code in [400, 422]


class TestUserRetrieval:
    """Tests for user retrieval."""
    
    def test_get_user_by_id(self, client: TestClient, unique_email: str) -> None:
        """Test getting user by ID."""
        # Create user
        create_response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "Test User",
            },
        )
        user_id = create_response.json()["id"]
        
        # Get user
        response = client.get(f"/api/v1/users/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == unique_email
    
    def test_get_user_not_found(self, client: TestClient) -> None:
        """Test 404 for non-existent user."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/users/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "USER_NOT_FOUND"
    
    def test_list_users(self, client: TestClient) -> None:
        """Test listing users with pagination."""
        response = client.get("/api/v1/users/?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestAuthentication:
    """Tests for authentication flow."""
    
    def test_login_success(self, client: TestClient, unique_email: str) -> None:
        """Test successful login returns tokens."""
        # Create user first
        client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "Test User",
            },
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "password123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "Bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, unique_email: str) -> None:
        """Test login with wrong password."""
        # Create user
        client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "correct_password",
                "name": "Test User",
            },
        )
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": unique_email,
                "password": "wrong_password",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_CREDENTIALS"
    
    def test_get_current_user_with_token(self, client: TestClient, unique_email: str) -> None:
        """Test /auth/me endpoint with valid token."""
        # Create user and login
        client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "Test User",
            },
        )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "password123"},
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == unique_email
    
    def test_get_current_user_without_token(self, client: TestClient) -> None:
        """Test /auth/me without token returns 401."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401


class TestUserUpdate:
    """Tests for user update operations."""
    
    def test_update_user_name(self, client: TestClient, unique_email: str) -> None:
        """Test updating user name."""
        # Create user
        create_response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "Original Name",
            },
        )
        user_id = create_response.json()["id"]
        
        # Update name
        response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"name": "Updated Name"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
    
    def test_deactivate_user(self, client: TestClient, unique_email: str) -> None:
        """Test deactivating user."""
        # Create user
        create_response = client.post(
            "/api/v1/users/",
            json={
                "email": unique_email,
                "password": "password123",
                "name": "Test User",
            },
        )
        user_id = create_response.json()["id"]
        
        # Deactivate
        response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] is False


class TestHealthCheck:
    """Tests for health check endpoints."""
    
    def test_liveness_probe(self, client: TestClient) -> None:
        """Test basic liveness probe."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_readiness_probe(self, client: TestClient) -> None:
        """Test readiness probe with DB check."""
        response = client.get("/health/ready")
        
        # Should be 200 if DB is available
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data

