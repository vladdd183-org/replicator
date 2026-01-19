"""E2E tests for complete user flows.

Tests realistic user scenarios from start to finish.
"""

import pytest
from litestar.testing import TestClient

from src.App import create_app


@pytest.fixture(scope="module")
def client():
    """Create test client with real app."""
    app = create_app()
    with TestClient(app=app) as client:
        yield client


class TestUserRegistrationAndAuthFlow:
    """E2E: Complete registration and authentication flow."""
    
    def test_full_user_lifecycle(self, client: TestClient) -> None:
        """Test complete user journey: register → login → use API → logout."""
        import uuid
        email = f"e2e_user_{uuid.uuid4().hex[:8]}@example.com"
        password = "secure_password_123"
        
        # 1. REGISTER: Create new user account
        register_response = client.post(
            "/api/v1/users/",
            json={
                "email": email,
                "password": password,
                "name": "E2E Test User",
            },
        )
        assert register_response.status_code == 201, f"Registration failed: {register_response.json()}"
        user_data = register_response.json()
        user_id = user_data["id"]
        
        # Verify user data
        assert user_data["email"] == email
        assert user_data["name"] == "E2E Test User"
        assert user_data["is_active"] is True
        
        # 2. LOGIN: Authenticate with credentials
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.json()}"
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Verify token structure
        assert tokens["token_type"] == "Bearer"
        assert "expires_in" in tokens
        
        # 3. ACCESS PROTECTED RESOURCE: Get current user
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_response.status_code == 200, f"Get me failed: {me_response.json()}"
        me_data = me_response.json()
        assert me_data["email"] == email
        assert me_data["id"] == user_id
        
        # 4. UPDATE PROFILE: Change user name
        update_response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"name": "Updated E2E User"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated E2E User"
        
        # 5. REFRESH TOKEN: Get new access token
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200, f"Refresh failed: {refresh_response.json()}"
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]
        
        # Verify new token works
        verify_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_access_token}"},
        )
        assert verify_response.status_code == 200
        
        # 6. LOGOUT
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # 7. VERIFY OLD TOKEN STILL WORKS (JWT is stateless)
        # In real app with blacklisting, this would return 401
        still_works = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        # This is expected behavior for stateless JWT
        assert still_works.status_code == 200
    
    def test_inactive_user_cannot_login(self, client: TestClient) -> None:
        """Test that deactivated users cannot log in."""
        import uuid
        email = f"inactive_{uuid.uuid4().hex[:8]}@example.com"
        password = "password123"
        
        # Create user
        create_response = client.post(
            "/api/v1/users/",
            json={"email": email, "password": password, "name": "Soon Inactive"},
        )
        user_id = create_response.json()["id"]
        
        # Verify login works initially
        login_ok = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_ok.status_code == 200
        
        # Deactivate user
        client.patch(f"/api/v1/users/{user_id}", json={"is_active": False})
        
        # Try to login again - should fail
        login_fail = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_fail.status_code == 403
        assert login_fail.json()["code"] == "USER_INACTIVE"


class TestPasswordManagement:
    """E2E: Password change flow."""
    
    def test_change_password_flow(self, client: TestClient) -> None:
        """Test changing password and logging in with new password."""
        import uuid
        email = f"pwd_change_{uuid.uuid4().hex[:8]}@example.com"
        old_password = "old_password_123"
        new_password = "new_password_456"
        
        # 1. Create user
        client.post(
            "/api/v1/users/",
            json={"email": email, "password": old_password, "name": "Password Changer"},
        )
        
        # 2. Login with old password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": old_password},
        )
        token = login_response.json()["access_token"]
        
        # 3. Change password
        change_response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": old_password,
                "new_password": new_password,
            },
        )
        assert change_response.status_code == 200
        
        # 4. Old password should NOT work
        old_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": old_password},
        )
        assert old_login.status_code == 401
        
        # 5. New password SHOULD work
        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": new_password},
        )
        assert new_login.status_code == 200


class TestAPIErrorHandling:
    """E2E: Error handling and Problem Details."""
    
    def test_problem_details_format(self, client: TestClient) -> None:
        """Test that errors follow RFC 9457 Problem Details format."""
        # Request non-existent user
        response = client.get("/api/v1/users/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        
        # RFC 9457 Problem Details fields
        assert "type" in data  # Error type URI
        assert "title" in data  # Human-readable title
        assert "status" in data  # HTTP status code
        assert "detail" in data  # Error message
        assert "code" in data  # Machine-readable code (extension)
    
    def test_validation_error_details(self, client: TestClient) -> None:
        """Test that validation errors include field details."""
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "invalid",
                "password": "123",  # Too short
                "name": "X",  # Too short
            },
        )
        
        # Litestar returns 400 for validation errors by default
        assert response.status_code in [400, 422]
        data = response.json()
        # Response should contain error info
        assert "errors" in data or "detail" in data or "extra" in data


class TestGraphQLIntegration:
    """E2E: GraphQL API integration."""
    
    def test_graphql_query_users(self, client: TestClient) -> None:
        """Test GraphQL users query."""
        query = """
        query {
            users(limit: 5) {
                users {
                    id
                    email
                    name
                }
                total
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={"query": query},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "users" in data["data"]
    
    def test_graphql_create_user_mutation(self, client: TestClient) -> None:
        """Test GraphQL createUser mutation."""
        import uuid
        email = f"graphql_{uuid.uuid4().hex[:8]}@example.com"
        
        mutation = """
        mutation CreateUser($input: CreateUserInput!) {
            createUser(input: $input) {
                user {
                    id
                    email
                    name
                }
                error {
                    message
                    code
                }
            }
        }
        """
        
        response = client.post(
            "/graphql",
            json={
                "query": mutation,
                "variables": {
                    "input": {
                        "email": email,
                        "password": "password123",
                        "name": "GraphQL User",
                    }
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["createUser"]["user"]["email"] == email

