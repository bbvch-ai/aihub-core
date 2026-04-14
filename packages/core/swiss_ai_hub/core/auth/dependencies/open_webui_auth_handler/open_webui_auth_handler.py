import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.auth_settings import AuthSettings
from swiss_ai_hub.core.auth.dependencies.bearer_auth_handler import BearerAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService

logger = logging.getLogger(__name__)


class OpenWebuiAuthHandler(AuthHandler):
    """
    A FastAPI dependency for OpenWebUI authentication.

    Validates HMAC signature from OpenWebUI headers and resolves user identity
    from the local database.
    """

    def __init__(self, base_auth_handler: BearerAuthHandler):
        """Initialize with a base auth handler to validate the bearer token."""
        self.base_auth_handler = base_auth_handler

        secret = AuthSettings().OPEN_WEBUI_SIGNING_SECRET.get_secret_value()
        self.signing_secret = secret.encode("utf-8")

    def _verify_signature(self, signature_to_check: str, user_name: str, user_email: str) -> bool:
        """Verifies the HMAC-SHA256 signature from OpenWebUI headers."""
        message = f"name:{user_name},email:{user_email}".encode()
        expected_signature = hmac.new(self.signing_secret, message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_signature, signature_to_check)

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        await self.base_auth_handler(request, bearer_token)

        user_name = request.headers.get("X-OpenWebUI-User-Name")
        user_email = request.headers.get("X-OpenWebUI-User-Email")
        signature = request.headers.get("X-OpenWebUI-Signature")

        if not (user_name and user_email and signature):
            raise HTTPException(
                status_code=400,
                detail="Required OpenWebUI headers are missing "
                "(X-OpenWebUI-User-Name, X-OpenWebUI-User-Email, X-OpenWebUI-Signature).",
            )

        is_signature_valid = self._verify_signature(signature, user_name, user_email)

        if not is_signature_valid:
            logger.warning("Invalid OpenWebUI signature for user. The request may be tampered.")
            raise HTTPException(status_code=401, detail="Invalid OpenWebUI signature.")

        logger.info("Successfully authenticated OpenWebUI user via signature")

        # Lookup existing user by email in Keycloak
        keycloak_user = await KeycloakAdminService.find_user_by_email(user_email)
        if not keycloak_user:
            logger.error(f"OpenWebUI user with email {user_email} not found in Keycloak")
            raise HTTPException(
                status_code=401,
                detail="User not found. Please login via OAuth2 before using OpenWebUI integration.",
            )

        return await self.build_identity(
            user_id=keycloak_user.id, name=keycloak_user.name, email=keycloak_user.email, request=request
        )

    async def authenticate_token(self, token: str) -> UserIdentity:
        """OpenWebuiAuthHandler requires request context and cannot be used for token-only authentication."""
        raise NotImplementedError("OpenWebuiAuthHandler does not support token authentication without request context")
