"""Integration tests for IdempotencyMiddleware.

Tests the full flow: HTTP request → Middleware → Cache → Response.
Uses Litestar TestClient with real middleware processing.
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock

from litestar import Litestar, post, get
from litestar.testing import TestClient
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_409_CONFLICT

from src.Ship.Middleware.Idempotency import IdempotencyMiddleware
from src.Ship.Infrastructure.Cache import cache, reset_cache_for_testing, setup_cache


# Test fixtures
@pytest.fixture(autouse=True)
def reset_cache():
    """Reset cache before each test."""
    reset_cache_for_testing()
    setup_cache()
    yield


@pytest.fixture
def unique_key() -> str:
    """Generate unique idempotency key for each test."""
    return f"test-{uuid.uuid4().hex[:16]}"


@pytest.fixture
def simple_app() -> Litestar:
    """Create a simple test app with idempotency middleware."""
    from litestar import Response
    from litestar.datastructures import State
    
    @post("/test", status_code=HTTP_200_OK)
    async def test_post(data: dict) -> dict:
        """Test POST endpoint returning 200."""
        return {"received": data, "id": str(uuid.uuid4())}
    
    @post("/test-201", status_code=HTTP_201_CREATED)
    async def test_post_201(data: dict) -> dict:
        """Test POST endpoint returning 201."""
        return {"created": True, "data": data}
    
    @get("/test")
    async def test_get() -> dict:
        """Test GET endpoint (should not be idempotent)."""
        return {"random": str(uuid.uuid4())}
    
    @post("/health", status_code=HTTP_200_OK)
    async def excluded_health(data: dict) -> dict:
        """Excluded endpoint - should not use idempotency."""
        return {"health": True}
    
    return Litestar(
        route_handlers=[test_post, test_post_201, test_get, excluded_health],
        middleware=[IdempotencyMiddleware],
    )


@pytest.fixture
def client(simple_app: Litestar) -> TestClient:
    """Create test client."""
    return TestClient(app=simple_app)


class TestIdempotencyBasicFlow:
    """Tests for basic idempotency flow."""
    
    def test_first_request_executes_normally(
        self, client: TestClient, unique_key: str
    ) -> None:
        """Test that first request with idempotency key executes normally."""
        response = client.post(
            "/test",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["received"] == {"value": 123}
        assert "id" in data
    
    def test_duplicate_request_returns_cached_response(
        self, client: TestClient, unique_key: str
    ) -> None:
        """Test that duplicate request returns cached response."""
        # First request
        response1 = client.post(
            "/test",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        data1 = response1.json()
        
        # Second request with same key
        response2 = client.post(
            "/test",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        data2 = response2.json()
        
        # Should return same response
        assert response2.status_code == HTTP_200_OK
        assert data1["id"] == data2["id"]  # Same ID = cached response
        
        # Should have replayed header
        assert response2.headers.get("X-Idempotency-Replayed") == "true"
    
    def test_different_keys_execute_separately(
        self, client: TestClient
    ) -> None:
        """Test that different keys result in different responses."""
        key1 = f"key-{uuid.uuid4().hex[:8]}"
        key2 = f"key-{uuid.uuid4().hex[:8]}"
        
        response1 = client.post(
            "/test",
            json={"value": 1},
            headers={"X-Idempotency-Key": key1},
        )
        
        response2 = client.post(
            "/test",
            json={"value": 2},
            headers={"X-Idempotency-Key": key2},
        )
        
        # Different IDs = different executions
        assert response1.json()["id"] != response2.json()["id"]


class TestIdempotencyWithoutKey:
    """Tests for requests without idempotency key."""
    
    def test_request_without_key_executes_normally(
        self, client: TestClient
    ) -> None:
        """Test that requests without key are processed normally."""
        response = client.post(
            "/test",
            json={"value": 123},
        )
        
        assert response.status_code == HTTP_200_OK
        assert "id" in response.json()
    
    def test_requests_without_key_are_not_deduplicated(
        self, client: TestClient
    ) -> None:
        """Test that requests without key are NOT deduplicated."""
        response1 = client.post("/test", json={"value": 1})
        response2 = client.post("/test", json={"value": 1})
        
        # Different IDs = different executions
        assert response1.json()["id"] != response2.json()["id"]


class TestIdempotencyMethodFiltering:
    """Tests for HTTP method filtering."""
    
    def test_get_requests_not_cached(self, client: TestClient) -> None:
        """Test that GET requests are not subject to idempotency."""
        key = f"key-{uuid.uuid4().hex[:8]}"
        
        response1 = client.get(
            "/test",
            headers={"X-Idempotency-Key": key},
        )
        
        response2 = client.get(
            "/test",
            headers={"X-Idempotency-Key": key},
        )
        
        # Different random values = different executions
        assert response1.json()["random"] != response2.json()["random"]
        
        # No replayed header (not cached)
        assert "X-Idempotency-Replayed" not in response2.headers


class TestIdempotencyConflictDetection:
    """Tests for request body conflict detection."""
    
    def test_different_body_same_key_returns_conflict(
        self, client: TestClient, unique_key: str
    ) -> None:
        """Test that different body with same key returns 409."""
        # First request
        client.post(
            "/test",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        # Second request with different body
        response = client.post(
            "/test",
            json={"value": 456},  # Different body!
            headers={"X-Idempotency-Key": unique_key},
        )
        
        assert response.status_code == HTTP_409_CONFLICT
        data = response.json()
        assert data["type"] == "urn:error:idempotency_conflict"


class TestIdempotencyKeyValidation:
    """Tests for idempotency key validation."""
    
    def test_valid_key_formats(self, client: TestClient) -> None:
        """Test various valid key formats."""
        valid_keys = [
            "simple",
            "with-dashes",
            "with_underscores",
            "MixedCase123",
            "a" * 256,  # Max length
        ]
        
        for key in valid_keys:
            response = client.post(
                "/test",
                json={"test": True},
                headers={"X-Idempotency-Key": key},
            )
            assert response.status_code == HTTP_200_OK, f"Key '{key}' should be valid"
    
    def test_invalid_key_with_spaces(self, client: TestClient) -> None:
        """Test that key with spaces is rejected."""
        response = client.post(
            "/test",
            json={"test": True},
            headers={"X-Idempotency-Key": "invalid key"},
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["type"].lower()
    
    def test_key_too_long(self, client: TestClient) -> None:
        """Test that key exceeding 256 chars is rejected."""
        long_key = "a" * 257
        
        response = client.post(
            "/test",
            json={"test": True},
            headers={"X-Idempotency-Key": long_key},
        )
        
        assert response.status_code == 400
        assert "too_long" in response.json()["type"].lower()


class TestIdempotencyPathExclusion:
    """Tests for path-based exclusion."""
    
    def test_excluded_path_bypasses_idempotency(
        self, client: TestClient, unique_key: str
    ) -> None:
        """Test that excluded paths don't use idempotency."""
        # /health is excluded by default
        response1 = client.post(
            "/health",
            json={"check": 1},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        response2 = client.post(
            "/health",
            json={"check": 2},  # Different body
            headers={"X-Idempotency-Key": unique_key},
        )
        
        # Should NOT return 409 (not checking idempotency)
        assert response1.status_code == HTTP_200_OK
        assert response2.status_code == HTTP_200_OK


class TestIdempotencyStatusCodePreservation:
    """Tests for HTTP status code preservation."""
    
    def test_201_status_preserved(
        self, client: TestClient, unique_key: str
    ) -> None:
        """Test that 201 status is preserved in cached response."""
        # First request
        response1 = client.post(
            "/test-201",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        assert response1.status_code == HTTP_201_CREATED
        
        # Second request (cached)
        response2 = client.post(
            "/test-201",
            json={"value": 123},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        # Status code should be preserved
        assert response2.status_code == HTTP_201_CREATED
        assert response2.headers.get("X-Idempotency-Replayed") == "true"


class TestIdempotencyHeaderCaseInsensitivity:
    """Tests for header name case handling."""
    
    def test_header_case_insensitive(
        self, client: TestClient
    ) -> None:
        """Test that header name is case-insensitive."""
        key = f"key-{uuid.uuid4().hex[:8]}"
        
        # First request with lowercase
        response1 = client.post(
            "/test",
            json={"value": 1},
            headers={"x-idempotency-key": key},  # lowercase
        )
        
        # Second request with mixed case
        response2 = client.post(
            "/test",
            json={"value": 1},
            headers={"X-Idempotency-Key": key},  # mixed case
        )
        
        # Should be same response (cached)
        assert response1.json()["id"] == response2.json()["id"]


class TestIdempotencyEnforcedPaths:
    """Tests for paths that require idempotency key."""
    
    @pytest.fixture
    def enforced_app(self) -> Litestar:
        """Create app with enforced idempotency paths."""
        
        @post("/api/v1/payments", status_code=HTTP_200_OK)
        async def create_payment(data: dict) -> dict:
            return {"payment_id": str(uuid.uuid4())}
        
        @post("/api/v1/users", status_code=HTTP_200_OK)
        async def create_user(data: dict) -> dict:
            return {"user_id": str(uuid.uuid4())}
        
        return Litestar(
            route_handlers=[create_payment, create_user],
            middleware=[
                IdempotencyMiddleware.create_config(
                    enforce_on_paths=["/api/v1/payments"],
                )
            ],
        )
    
    @pytest.fixture
    def enforced_client(self, enforced_app: Litestar) -> TestClient:
        """Create client for enforced app."""
        return TestClient(app=enforced_app)
    
    def test_enforced_path_requires_key(
        self, enforced_client: TestClient
    ) -> None:
        """Test that enforced path without key returns 400."""
        response = enforced_client.post(
            "/api/v1/payments",
            json={"amount": 100},
        )
        
        assert response.status_code == 400
        assert "required" in response.json()["type"].lower()
    
    def test_enforced_path_with_key_works(
        self, enforced_client: TestClient, unique_key: str
    ) -> None:
        """Test that enforced path with key works normally."""
        response = enforced_client.post(
            "/api/v1/payments",
            json={"amount": 100},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        assert response.status_code == HTTP_200_OK
        assert "payment_id" in response.json()
    
    def test_non_enforced_path_works_without_key(
        self, enforced_client: TestClient
    ) -> None:
        """Test that non-enforced path works without key."""
        response = enforced_client.post(
            "/api/v1/users",
            json={"name": "Test"},
        )
        
        assert response.status_code == HTTP_200_OK


class TestIdempotencyCustomTTL:
    """Tests for custom TTL configuration."""
    
    @pytest.fixture
    def short_ttl_app(self) -> Litestar:
        """Create app with short TTL."""
        
        @post("/test", status_code=HTTP_200_OK)
        async def test_endpoint(data: dict) -> dict:
            return {"id": str(uuid.uuid4())}
        
        return Litestar(
            route_handlers=[test_endpoint],
            middleware=[
                IdempotencyMiddleware.create_config(ttl_seconds=1)
            ],
        )
    
    @pytest.fixture
    def short_ttl_client(self, short_ttl_app: Litestar) -> TestClient:
        """Create client for short TTL app."""
        return TestClient(app=short_ttl_app)
    
    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(
        self, short_ttl_client: TestClient, unique_key: str
    ) -> None:
        """Test that cache expires after TTL."""
        import asyncio
        
        # First request
        response1 = short_ttl_client.post(
            "/test",
            json={"value": 1},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        # Wait for TTL to expire
        await asyncio.sleep(1.5)
        
        # Second request - should get new response (cache expired)
        response2 = short_ttl_client.post(
            "/test",
            json={"value": 1},
            headers={"X-Idempotency-Key": unique_key},
        )
        
        # Different IDs = cache expired, new execution
        # Note: This test may be flaky due to timing
        # In production, TTL would be much longer
        assert response1.json()["id"] != response2.json()["id"]
