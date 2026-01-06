from aihub_lib.auth.identity.UserIdentity import UserIdentity
from pydantic import SecretStr

from aihub_mcp.auth.ApiKeyAuth import ApiKeyAuth


class TestApiKeyAuth:
    """Tests for ApiKeyAuth class."""

    def test_disabled_when_no_key(self) -> None:
        """Test that auth is disabled when no key is provided."""
        auth = ApiKeyAuth(api_key=None)
        assert auth.enabled is False
        assert auth.validate({}) is True

    def test_enabled_with_single_key(self) -> None:
        """Test that auth is enabled with a single key."""
        auth = ApiKeyAuth(api_key=SecretStr("test-key"))
        assert auth.enabled is True

    def test_validate_correct_key(self) -> None:
        """Test validation with correct API key."""
        auth = ApiKeyAuth(api_key=SecretStr("secret-key"))
        headers = {"X-API-Key": "secret-key"}
        assert auth.validate(headers) is True

    def test_validate_incorrect_key(self) -> None:
        """Test validation with incorrect API key."""
        auth = ApiKeyAuth(api_key=SecretStr("secret-key"))
        headers = {"X-API-Key": "wrong-key"}
        assert auth.validate(headers) is False

    def test_validate_missing_key(self) -> None:
        """Test validation with missing API key."""
        auth = ApiKeyAuth(api_key=SecretStr("secret-key"))
        headers: dict[str, str] = {}
        assert auth.validate(headers) is False

    def test_validate_bearer_token(self) -> None:
        """Test validation with Bearer token in Authorization header."""
        auth = ApiKeyAuth(api_key=SecretStr("secret-key"))
        headers = {"Authorization": "Bearer secret-key"}
        assert auth.validate(headers) is True

    def test_validate_wrong_bearer_token(self) -> None:
        """Test validation with wrong Bearer token."""
        auth = ApiKeyAuth(api_key=SecretStr("secret-key"))
        headers = {"Authorization": "Bearer wrong-key"}
        assert auth.validate(headers) is False

    def test_get_user_identity_with_key(self) -> None:
        """Test getting user identity when auth is enabled."""
        auth = ApiKeyAuth(api_key=SecretStr("test-key"))
        identity = auth.get_user_identity()

        assert identity.id.startswith("mcp_client_")

    def test_get_user_identity_no_auth(self) -> None:
        """Test getting user identity when auth is disabled."""
        auth = ApiKeyAuth(api_key=None)
        identity = auth.get_user_identity()

        assert identity.id == "anonymous"


class TestUserIdentity:
    """Tests for UserIdentity from aihub_lib."""

    def test_user_identity_fields(self) -> None:
        """Test UserIdentity field access."""
        identity = UserIdentity(
            id="test",
            name="Test User",
            email="test@example.com",
            roles=["admin"],
        )
        assert identity.id == "test"
        assert identity.name == "Test User"
        assert identity.email == "test@example.com"
        assert identity.roles == ["admin"]

    def test_model_dump(self) -> None:
        """Test conversion to dictionary via model_dump."""
        identity = UserIdentity(
            id="test",
            name="Test User",
            email="test@example.com",
            roles=["admin"],
        )
        d = identity.model_dump()

        assert d["id"] == "test"
        assert d["name"] == "Test User"
        assert d["email"] == "test@example.com"
        assert d["roles"] == ["admin"]
