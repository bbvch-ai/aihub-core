import hashlib
import hmac
import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mongoengine import DoesNotExist

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.AuthSettings import AuthSettings
from aihub_lib.auth.dependencies.BearerAuthHandler import BearerAuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.persistence.user.UserEntity import UserEntity

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

        # Lookup existing user by email
        # OpenWebUI users must have previously logged in via OAuth2
        try:
            user_entity = UserEntity.by_email(user_email)
        except DoesNotExist:
            logger.error(f"OpenWebUI user with email {user_email} not found in database")
            raise HTTPException(
                status_code=401,
                detail="User not found. Please login via OAuth2 before using OpenWebUI integration.",
            )

        # Resolve tenant context from request
        tenant = self.resolve_tenant_for_user(request, user_entity.id)

        return UserIdentity.from_user_entity(user_entity, tenant)

    async def authenticate_token(self, token: str) -> UserIdentity:
        """OpenWebuiAuthHandler requires request context and cannot be used for token-only authentication."""
        raise NotImplementedError("OpenWebuiAuthHandler does not support token authentication without request context")
