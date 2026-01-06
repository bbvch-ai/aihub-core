import hashlib
import logging
import secrets

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from pydantic import SecretStr

logger = logging.getLogger(__name__)


def _short_hash(key: str) -> str:
    """Create a short deterministic identifier from a key (for logging, not security)."""
    return hashlib.sha256(key.encode()).hexdigest()[:8]


class ApiKeyAuth:
    """
    API key authentication for MCP server.

    Uses constant-time comparison to prevent timing attacks.
    """

    def __init__(self, api_keys: list[SecretStr] | SecretStr | None = None) -> None:
        self._key_to_identity: dict[str, UserIdentity] = {}
        self._enabled = False

        if api_keys is not None:
            keys = [api_keys] if isinstance(api_keys, SecretStr) else api_keys
            for key in keys:
                self._register_key(key)

    def _register_key(self, key: SecretStr) -> None:
        """Register an API key with auto-generated identity."""
        key_value = key.get_secret_value()
        short_id = _short_hash(key_value)

        self._key_to_identity[key_value] = UserIdentity(
            id=f"mcp_client_{short_id}",
            name=f"MCP Client ({short_id})",
            email=f"mcp_{short_id}@aihub.local",
            roles=["user"],
        )
        self._enabled = True
        logger.info(f"Registered API key: {short_id}")

    @property
    def enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self._enabled

    def validate(self, headers: dict[str, str]) -> bool:
        """Validate the API key from request headers."""
        if not self._enabled:
            return True

        api_key = self._extract_key(headers)
        if not api_key:
            logger.warning("No API key provided in request")
            return False

        if self._validate_key(api_key) is None:
            logger.warning("Invalid API key provided")
            return False

        return True

    def _extract_key(self, headers: dict[str, str]) -> str | None:
        """Extract API key from headers (case-insensitive lookup)."""
        lower_headers = {k.lower(): v for k, v in headers.items()}

        if api_key := lower_headers.get("x-api-key"):
            return api_key

        auth_header = lower_headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        return None

    def _validate_key(self, provided_key: str) -> UserIdentity | None:
        """Validate and return identity using constant-time comparison to prevent timing attacks."""
        for valid_key, identity in self._key_to_identity.items():
            if secrets.compare_digest(provided_key, valid_key):
                return identity
        return None

    def get_user_identity(self, headers: dict[str, str]) -> UserIdentity:
        """Get the user identity for an authenticated request."""
        if not self._enabled:
            return UserIdentity(
                id="anonymous",
                name="Anonymous (Auth Disabled)",
                email="anonymous@aihub.local",
                roles=["user"],
            )

        api_key = self._extract_key(headers)
        if api_key:
            identity = self._validate_key(api_key)
            if identity:
                return identity

        return UserIdentity(
            id="unknown",
            name="Unknown Client",
            email="unknown@aihub.local",
            roles=["user"],
        )
