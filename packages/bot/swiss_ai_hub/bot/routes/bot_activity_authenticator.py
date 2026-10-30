import logging

from fastapi import HTTPException, Request
from jwt import PyJWTError
from microsoft_agents.hosting.core import AgentAuthConfiguration, ClaimsIdentity
from microsoft_agents.hosting.core.authorization import JwtTokenValidator
from microsoft_agents.hosting.core.authorization.authentication_constants import AuthenticationConstants

logger = logging.getLogger(__name__)


class BotActivityAuthenticator:
    """
    Verifies that an inbound activity was sent by the Azure Bot Service for the bot configured on its path.

    The SDK's `CloudAdapter` silently falls back to anonymous claims when no JWT middleware runs, and its
    `JwtTokenValidator` checks only signature and audience. The issuer, the caller and the `serviceurl` claim are
    checked here as well, so a token cannot be replayed against another service URL or minted by another app.
    """

    BEARER_PREFIX = "Bearer "

    @staticmethod
    async def authenticate(
        request: Request,
        auth_configuration: AgentAuthConfiguration,
    ) -> ClaimsIdentity:
        token = BotActivityAuthenticator._bearer_token(request)
        try:
            claims_identity = await JwtTokenValidator(auth_configuration).validate_token(token)
        except (ValueError, KeyError, PyJWTError) as invalid_token_error:
            logger.warning(f"Rejected bot activity with an invalid token: {invalid_token_error}")
            raise BotActivityAuthenticator._unauthorized("Invalid bot activity token.") from invalid_token_error

        BotActivityAuthenticator._assert_trusted_issuer(claims_identity, auth_configuration)
        BotActivityAuthenticator._assert_channel_caller(claims_identity)
        await BotActivityAuthenticator._assert_service_url_matches(request, claims_identity)
        return claims_identity

    @staticmethod
    def _bearer_token(request: Request) -> str:
        authorization_header = request.headers.get("Authorization", "")
        if not authorization_header.startswith(BotActivityAuthenticator.BEARER_PREFIX):
            raise BotActivityAuthenticator._unauthorized("Missing bot activity token.")
        return authorization_header.removeprefix(BotActivityAuthenticator.BEARER_PREFIX).strip()

    @staticmethod
    def _assert_trusted_issuer(claims_identity: ClaimsIdentity, auth_configuration: AgentAuthConfiguration) -> None:
        issuer = claims_identity.get_claim_value(AuthenticationConstants.ISSUER_CLAIM)
        if issuer not in auth_configuration.ISSUERS:
            logger.warning(f"Rejected bot activity token from untrusted issuer {issuer!r}")
            raise BotActivityAuthenticator._unauthorized("Untrusted bot activity token issuer.")

    @staticmethod
    def _assert_channel_caller(claims_identity: ClaimsIdentity) -> None:
        """Agent-to-agent tokens are issued to other apps, so they must not reach the user-facing bot routes."""
        if claims_identity.is_agent_claim():
            logger.warning("Rejected bot activity token issued to another application")
            raise BotActivityAuthenticator._unauthorized("Bot activity token was not issued by a channel.")

    @staticmethod
    async def _assert_service_url_matches(request: Request, claims_identity: ClaimsIdentity) -> None:
        token_service_url = claims_identity.get_claim_value(AuthenticationConstants.SERVICE_URL_CLAIM)
        activity_service_url = (await request.json()).get("serviceUrl")
        if not token_service_url or not activity_service_url:
            raise BotActivityAuthenticator._unauthorized("Bot activity token does not name a service URL.")
        if token_service_url.rstrip("/").lower() != activity_service_url.rstrip("/").lower():
            logger.warning(f"Rejected bot activity for {activity_service_url!r}, token is for {token_service_url!r}")
            raise BotActivityAuthenticator._unauthorized("Bot activity service URL does not match its token.")

    @staticmethod
    def _unauthorized(detail: str) -> HTTPException:
        return HTTPException(status_code=401, detail=detail)
