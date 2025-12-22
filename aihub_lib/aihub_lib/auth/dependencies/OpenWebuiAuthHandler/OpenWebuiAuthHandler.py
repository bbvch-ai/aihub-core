import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.AuthSettings import AuthSettings
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class OpenWebuiAuthHandler:
    """
    A FastAPI dependency for OpenWebUI authentication.

    Validates HMAC signature from OpenWebUI headers and fetches user identity
    by email from Azure Graph.
    """

    def __init__(self, base_auth_handler):
        """
        Args:
            base_auth_handler: The auth handler to validate the bearer token.
        """
        self.base_auth_handler = base_auth_handler
        self.oauth2_handler = OAuth2AuthHandler()

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
        return await self.oauth2_handler.get_user_identity_by_email(user_email)

    async def authenticate_token(self, token_str: str) -> UserIdentity:
        raise NotImplementedError("OpenWebuiAuthHandler does not support token authentication without request context")
