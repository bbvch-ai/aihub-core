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

    def __init__(self, api_key: SecretStr | None = None) -> None:
        self._identity: UserIdentity | None = None
        self._key: str | None = None

        if api_key is not None:
            self._key = api_key.get_secret_value()
            short_id = _short_hash(self._key)
            self._identity = UserIdentity(
                id=f"mcp_client_{short_id}",
                name=f"MCP Client ({short_id})",
                email=f"mcp_{short_id}@aihub.local",
                roles=["user"],
            )
            logger.info(f"Registered API key: {short_id}")

    @property
    def enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self._key is not None

    def validate(self, headers: dict[str, str]) -> bool:
        """Validate the API key from request headers."""
        if not self.enabled:
            return True

        api_key = self._extract_key(headers)
        if not api_key:
            logger.warning("No API key provided in request")
            return False

        if self._key is None or not secrets.compare_digest(api_key, self._key):
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

    def get_user_identity(self) -> UserIdentity:
        """Get the user identity for an authenticated request."""
        if not self.enabled or self._identity is None:
            return UserIdentity(
                id="anonymous",
                name="Anonymous (Auth Disabled)",
                email="anonymous@aihub.local",
                roles=["user"],
            )

        return self._identity
