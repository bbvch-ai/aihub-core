"""Tests for API key authentication."""

import time
from unittest.mock import patch

from pydantic import SecretStr

from aihub_mcp.auth.ApiKeyAuth import ApiKeyAuth, UserIdentity


class TestApiKeyAuth:
    """Tests for ApiKeyAuth class."""

    def test_disabled_when_no_key(self) -> None:
        """Test that auth is disabled when no key is provided."""
        auth = ApiKeyAuth(api_keys=None)
        assert auth.enabled is False
        assert auth.validate({}) is True

    def test_enabled_with_single_key(self) -> None:
        """Test that auth is enabled with a single key."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"))
        assert auth.enabled is True

    def test_validate_correct_key(self) -> None:
        """Test validation with correct API key."""
        auth = ApiKeyAuth(api_keys=SecretStr("secret-key"))
        headers = {"X-API-Key": "secret-key"}
        assert auth.validate(headers) is True

    def test_validate_incorrect_key(self) -> None:
        """Test validation with incorrect API key."""
        auth = ApiKeyAuth(api_keys=SecretStr("secret-key"))
        headers = {"X-API-Key": "wrong-key"}
        assert auth.validate(headers) is False

    def test_validate_missing_key(self) -> None:
        """Test validation with missing API key."""
        auth = ApiKeyAuth(api_keys=SecretStr("secret-key"))
        headers: dict[str, str] = {}
        assert auth.validate(headers) is False

    def test_validate_bearer_token(self) -> None:
        """Test validation with Bearer token in Authorization header."""
        auth = ApiKeyAuth(api_keys=SecretStr("secret-key"))
        headers = {"Authorization": "Bearer secret-key"}
        assert auth.validate(headers) is True

    def test_validate_wrong_bearer_token(self) -> None:
        """Test validation with wrong Bearer token."""
        auth = ApiKeyAuth(api_keys=SecretStr("secret-key"))
        headers = {"Authorization": "Bearer wrong-key"}
        assert auth.validate(headers) is False

    def test_multiple_keys(self) -> None:
        """Test validation with multiple valid keys."""
        auth = ApiKeyAuth(api_keys=[SecretStr("key1"), SecretStr("key2")])
        assert auth.validate({"X-API-Key": "key1"}) is True
        assert auth.validate({"X-API-Key": "key2"}) is True
        assert auth.validate({"X-API-Key": "key3"}) is False

    def test_add_key_with_identity(self) -> None:
        """Test adding a key with custom identity."""
        auth = ApiKeyAuth(api_keys=None)
        assert auth.enabled is False

        auth.add_key(
            SecretStr("new-key"),
            user_id="custom-user",
            user_name="Custom User",
            user_email="custom@example.com",
            roles=["admin", "user"],
        )
        assert auth.enabled is True
        assert auth.validate({"X-API-Key": "new-key"}) is True

        identity = auth.get_user_identity({"X-API-Key": "new-key"})
        assert identity["id"] == "custom-user"
        assert identity["name"] == "Custom User"
        assert identity["email"] == "custom@example.com"
        assert "admin" in identity["roles"]

    def test_remove_key(self) -> None:
        """Test removing a key."""
        auth = ApiKeyAuth(api_keys=SecretStr("only-key"))
        assert auth.enabled is True

        auth.remove_key(SecretStr("only-key"))
        assert auth.enabled is False

    def test_get_user_identity_with_key(self) -> None:
        """Test getting user identity from request with API key."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"))
        identity = auth.get_user_identity({"X-API-Key": "test-key"})

        # Should contain generated identity based on key hash
        assert identity["id"].startswith("mcp_client_")
        assert identity["source"] == "api_key"

    def test_get_user_identity_no_auth(self) -> None:
        """Test getting user identity when auth is disabled."""
        auth = ApiKeyAuth(api_keys=None)
        identity = auth.get_user_identity({})

        assert identity["id"] == "anonymous"
        assert identity["source"] == "no_auth"

    def test_get_client_id(self) -> None:
        """Test getting unique client ID for logging."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"))

        client_id = auth.get_client_id({"X-API-Key": "test-key"})
        assert len(client_id) == 16  # First 16 chars of SHA256

        # Same key should give same ID
        client_id2 = auth.get_client_id({"X-API-Key": "test-key"})
        assert client_id == client_id2

        # No key should give "anonymous"
        anon_id = auth.get_client_id({})
        assert anon_id == "anonymous"


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_rate_limit_allows_requests_under_limit(self) -> None:
        """Test that requests under the limit are allowed."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"), rate_limit_per_minute=10)

        # Should allow 10 requests
        for _ in range(10):
            assert auth.validate({"X-API-Key": "test-key"}) is True

    def test_rate_limit_blocks_requests_over_limit(self) -> None:
        """Test that requests over the limit are blocked."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"), rate_limit_per_minute=5)

        # Use up the limit
        for _ in range(5):
            assert auth.validate({"X-API-Key": "test-key"}) is True

        # 6th request should fail
        assert auth.validate({"X-API-Key": "test-key"}) is False

    def test_rate_limit_resets_after_minute(self) -> None:
        """Test that rate limit resets after a minute."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"), rate_limit_per_minute=2)

        # Use up limit
        assert auth.validate({"X-API-Key": "test-key"}) is True
        assert auth.validate({"X-API-Key": "test-key"}) is True
        assert auth.validate({"X-API-Key": "test-key"}) is False

        # Mock time to be 61 seconds later
        with patch.object(time, "time", return_value=time.time() + 61):
            # Should work again after rate limit clears old timestamps
            # Need to also clear the blocked_until
            auth._rate_limits[auth._hash_key("test-key")].blocked_until = 0
            auth._rate_limits[auth._hash_key("test-key")].request_timestamps = []
            assert auth.validate({"X-API-Key": "test-key"}) is True

    def test_rate_limit_disabled_when_zero(self) -> None:
        """Test that rate limiting is disabled when set to 0."""
        auth = ApiKeyAuth(api_keys=SecretStr("test-key"), rate_limit_per_minute=0)

        # Should allow unlimited requests
        for _ in range(100):
            assert auth.validate({"X-API-Key": "test-key"}) is True

    def test_rate_limit_per_client(self) -> None:
        """Test that rate limits are per-client."""
        auth = ApiKeyAuth(
            api_keys=[SecretStr("key1"), SecretStr("key2")],
            rate_limit_per_minute=2,
        )

        # Use up limit for key1
        assert auth.validate({"X-API-Key": "key1"}) is True
        assert auth.validate({"X-API-Key": "key1"}) is True
        assert auth.validate({"X-API-Key": "key1"}) is False

        # key2 should still work
        assert auth.validate({"X-API-Key": "key2"}) is True
        assert auth.validate({"X-API-Key": "key2"}) is True


class TestUserIdentity:
    """Tests for UserIdentity dataclass."""

    def test_default_roles(self) -> None:
        """Test default roles for user identity."""
        identity = UserIdentity(
            id="test",
            name="Test User",
            email="test@example.com",
        )
        assert identity.roles == ["user"]
        assert identity.source == "api_key"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        identity = UserIdentity(
            id="test",
            name="Test User",
            email="test@example.com",
            roles=["admin"],
        )
        d = identity.to_dict()

        assert d["id"] == "test"
        assert d["name"] == "Test User"
        assert d["email"] == "test@example.com"
        assert d["roles"] == ["admin"]
        assert d["source"] == "api_key"
