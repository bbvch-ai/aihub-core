"""Tests for API key authentication."""

from pydantic import SecretStr

from aihub_mcp.auth.ApiKeyAuth import ApiKeyAuth


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

    def test_add_key(self) -> None:
        """Test adding a key dynamically."""
        auth = ApiKeyAuth(api_keys=None)
        assert auth.enabled is False

        auth.add_key(SecretStr("new-key"))
        assert auth.enabled is True
        assert auth.validate({"X-API-Key": "new-key"}) is True

    def test_remove_key(self) -> None:
        """Test removing a key."""
        auth = ApiKeyAuth(api_keys=SecretStr("only-key"))
        assert auth.enabled is True

        auth.remove_key(SecretStr("only-key"))
        assert auth.enabled is False

    def test_get_user_identity(self) -> None:
        """Test getting user identity from request."""
        auth = ApiKeyAuth(api_keys=SecretStr("key"))
        identity = auth.get_user_identity({})

        assert identity["id"] == "mcp_client"
        assert identity["source"] == "api_key"
