"""API key authentication for MCP requests."""

import hashlib
import logging
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from pydantic import SecretStr

logger = logging.getLogger(__name__)


@dataclass
class UserIdentity:
    """User identity associated with an API key."""

    id: str
    name: str
    email: str
    roles: list[str] = field(default_factory=lambda: ["user"])
    source: str = "api_key"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for SAAP events."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "roles": self.roles,
            "source": self.source,
        }


@dataclass
class RateLimitState:
    """Track rate limiting state for a client."""

    request_timestamps: list[float] = field(default_factory=list)
    blocked_until: float = 0.0


class ApiKeyAuth:
    """
    API key authentication for MCP server.

    Validates API keys from request headers against configured keys.
    Supports multiple API keys for different clients with identity mapping.

    Security features:
    - Constant-time key comparison (timing attack prevention)
    - Per-client rate limiting
    - API key to user identity mapping
    - Request logging for audit trail
    """

    HEADER_NAME = "X-API-Key"
    BEARER_PREFIX = "Bearer "
    DEFAULT_RATE_LIMIT = 60  # requests per minute

    def __init__(
        self,
        api_keys: list[SecretStr] | SecretStr | None = None,
        rate_limit_per_minute: int = DEFAULT_RATE_LIMIT,
    ) -> None:
        """
        Initialize with configured API keys.

        If api_keys is None or empty, authentication is disabled.
        """
        self._key_to_identity: dict[str, UserIdentity] = {}
        self._rate_limits: dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._rate_limit_per_minute = rate_limit_per_minute
        self._enabled = False

        if api_keys is not None:
            if isinstance(api_keys, SecretStr):
                self._register_key(api_keys)
            else:
                for key in api_keys:
                    self._register_key(key)

    def _register_key(self, key: SecretStr, identity: UserIdentity | None = None) -> None:
        """Register an API key with optional identity mapping."""
        key_value = key.get_secret_value()
        key_hash = self._hash_key(key_value)

        if identity is None:
            # Generate default identity from key hash
            short_id = key_hash[:8]
            identity = UserIdentity(
                id=f"mcp_client_{short_id}",
                name=f"MCP Client ({short_id})",
                email=f"mcp_{short_id}@aihub.local",
            )

        self._key_to_identity[key_value] = identity
        self._enabled = True
        logger.info(f"Registered API key for user: {identity.id}")

    def _hash_key(self, key: str) -> str:
        """Create a safe hash of the key for logging/identification."""
        return hashlib.sha256(key.encode()).hexdigest()

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

        # Extract API key
        api_key = self._extract_key(headers)
        if not api_key:
            logger.warning("No API key provided in request")
            return False

        # Validate key
        if not self._validate_key(api_key):
            logger.warning("Invalid API key provided")
            return False

        # Check rate limit
        if not self._check_rate_limit(api_key):
            logger.warning(f"Rate limit exceeded for client {self._hash_key(api_key)[:8]}")
            return False

        return True

    def _extract_key(self, headers: dict[str, str]) -> str | None:
        """Extract API key from headers."""
        # Check X-API-Key header
        api_key = headers.get(self.HEADER_NAME)
        if api_key:
            return api_key

        # Check Authorization header (Bearer token)
        auth_header = headers.get("Authorization", "")
        if auth_header.startswith(self.BEARER_PREFIX):
            return auth_header[len(self.BEARER_PREFIX) :]

        return None

    def _validate_key(self, provided_key: str) -> bool:
        """Validate a provided key against stored keys using constant-time comparison."""
        for valid_key in self._key_to_identity:
            if secrets.compare_digest(provided_key, valid_key):
                return True
        return False

    def _check_rate_limit(self, api_key: str) -> bool:
        """Check if client is within rate limits."""
        if self._rate_limit_per_minute <= 0:
            return True  # Rate limiting disabled

        key_hash = self._hash_key(api_key)
        state = self._rate_limits[key_hash]
        now = time.time()

        # Check if blocked
        if now < state.blocked_until:
            return False

        # Clean old timestamps (older than 1 minute)
        cutoff = now - 60.0
        state.request_timestamps = [ts for ts in state.request_timestamps if ts > cutoff]

        # Check rate limit
        if len(state.request_timestamps) >= self._rate_limit_per_minute:
            state.blocked_until = now + 60.0  # Block for 1 minute
            return False

        # Record this request
        state.request_timestamps.append(now)
        return True

    def add_key(
        self,
        key: SecretStr,
        user_id: str | None = None,
        user_name: str | None = None,
        user_email: str | None = None,
        roles: list[str] | None = None,
    ) -> None:
        """Add an API key with optional user identity."""
        identity = None
        if user_id or user_name or user_email:
            identity = UserIdentity(
                id=user_id or "mcp_client",
                name=user_name or "MCP Client",
                email=user_email or "mcp@aihub.local",
                roles=roles or ["user"],
            )
        self._register_key(key, identity)

    def remove_key(self, key: SecretStr) -> None:
        """Remove an API key."""
        key_value = key.get_secret_value()
        if key_value in self._key_to_identity:
            del self._key_to_identity[key_value]
            logger.info(f"Removed API key: {self._hash_key(key_value)[:8]}")

        if not self._key_to_identity:
            self._enabled = False

    def get_user_identity(self, headers: dict[str, str]) -> dict[str, Any]:
        """
        Extract user identity from authenticated request.

        Returns the identity mapped to the API key, or a default identity
        if authentication is disabled.
        """
        if not self._enabled:
            return {
                "id": "anonymous",
                "name": "Anonymous (Auth Disabled)",
                "email": "anonymous@aihub.local",
                "roles": ["user"],
                "source": "no_auth",
            }

        api_key = self._extract_key(headers)
        if api_key and api_key in self._key_to_identity:
            return self._key_to_identity[api_key].to_dict()

        # Fallback (should not reach here if validate() was called first)
        return {
            "id": "unknown",
            "name": "Unknown Client",
            "email": "unknown@aihub.local",
            "roles": ["user"],
            "source": "api_key",
        }

    def get_client_id(self, headers: dict[str, str]) -> str:
        """Get a unique client identifier for rate limiting and logging."""
        api_key = self._extract_key(headers)
        if api_key:
            return self._hash_key(api_key)[:16]
        return "anonymous"
