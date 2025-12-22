"""API key authentication for MCP requests."""

import logging
import secrets
from typing import Any

from pydantic import SecretStr

logger = logging.getLogger(__name__)


class ApiKeyAuth:
    """
    API key authentication for MCP server.

    Validates API keys from request headers against configured keys.
    Supports multiple API keys for different clients.
    """

    HEADER_NAME = "X-API-Key"
    BEARER_PREFIX = "Bearer "

    def __init__(self, api_keys: list[SecretStr] | SecretStr | None = None) -> None:
        """
        Initialize with configured API keys.

        If api_keys is None, authentication is disabled.
        """
        if api_keys is None:
            self._keys: set[str] = set()
            self._enabled = False
        elif isinstance(api_keys, SecretStr):
            self._keys = {api_keys.get_secret_value()}
            self._enabled = True
        else:
            self._keys = {k.get_secret_value() for k in api_keys}
            self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if authentication is enabled."""
        return self._enabled

    def validate(self, headers: dict[str, str]) -> bool:
        """
        Validate the API key from request headers.

        Returns True if valid or if auth is disabled.
        """
        if not self._enabled:
            return True

        # Check X-API-Key header
        api_key = headers.get(self.HEADER_NAME)
        if api_key:
            return self._validate_key(api_key)

        # Check Authorization header (Bearer token)
        auth_header = headers.get("Authorization", "")
        if auth_header.startswith(self.BEARER_PREFIX):
            token = auth_header[len(self.BEARER_PREFIX) :]
            return self._validate_key(token)

        logger.warning("No API key provided in request")
        return False

    def _validate_key(self, provided_key: str) -> bool:
        """Validate a provided key against stored keys using constant-time comparison."""
        for valid_key in self._keys:
            if secrets.compare_digest(provided_key, valid_key):
                return True
        logger.warning("Invalid API key provided")
        return False

    def add_key(self, key: SecretStr) -> None:
        """Add an API key dynamically."""
        self._keys.add(key.get_secret_value())
        self._enabled = True

    def remove_key(self, key: SecretStr) -> None:
        """Remove an API key."""
        self._keys.discard(key.get_secret_value())
        if not self._keys:
            self._enabled = False

    def get_user_identity(self, headers: dict[str, str]) -> dict[str, Any]:
        """
        Extract user identity from authenticated request.

        For now, returns a generic MCP client identity.
        Could be extended to map API keys to specific users.
        """
        return {
            "id": "mcp_client",
            "name": "MCP Client",
            "email": "mcp@aihub.local",
            "source": "api_key",
        }
