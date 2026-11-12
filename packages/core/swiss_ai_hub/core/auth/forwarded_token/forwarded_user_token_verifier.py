import logging
from typing import Annotated

from fastapi import HTTPException

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.tracing.nats_message_headers import NATSMessageHeaders

logger = logging.getLogger(__name__)


class ForwardedUserTokenVerifier:
    """Admit a client-supplied user token onto the agent pipeline only when it is the requesting user's own.

    MCP profiles with ``auth_mode: user_token`` send this token to an external MCP server as the user's proof of
    identity. Unchecked, a client authenticated as one user could start a run that acts as another, so the API
    verifies the token before it reaches NATS. Until runs get their own token (#2121), this is the user's Keycloak
    access token.
    """

    @staticmethod
    async def verified_aihub_headers(
        request_headers: Annotated[dict[str, str], "The HTTP request's headers."],
        user: Annotated[UserIdentity, "The user the request authenticated as."],
    ) -> dict[str, str]:
        """Return the request's ``X-AIHub-*`` headers, refusing a user token that is not this user's."""
        aihub_headers = NATSMessageHeaders.extract_aihub_headers(request_headers)
        user_token = aihub_headers.get(NATSMessageHeaders.USER_TOKEN_HEADER)
        if user_token is not None:
            await ForwardedUserTokenVerifier._ensure_token_of(user_token, user)
        return aihub_headers

    @staticmethod
    async def _ensure_token_of(user_token: str, user: UserIdentity) -> None:
        # Imported here: the handler builds KeycloakSettings when its module loads, which needs KEYCLOAK_URL even in
        # services and tests that never receive a forwarded token.
        from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import (
            KeycloakAuthHandler,
        )

        # No audience check: OpenWebUI's tokens carry none (azp "openwebui"), and the API never acts on this token
        # itself; it only confirms the token is a valid realm token of the requesting user.
        claims = await KeycloakAuthHandler().decode_token(user_token, audience=None)
        if claims.get("sub") != user.id:
            logger.warning("Refused a forwarded user token that belongs to another user than %s", user.id)
            raise HTTPException(
                status_code=401, detail="The forwarded user token does not belong to the requesting user"
            )
