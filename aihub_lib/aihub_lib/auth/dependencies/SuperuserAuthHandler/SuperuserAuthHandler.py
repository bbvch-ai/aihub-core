import logging

from fastapi import HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from aihub_lib.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
from aihub_lib.auth.identity.TenantIdentity import TenantIdentity
from aihub_lib.auth.identity.UserIdentity import UserIdentity

logger = logging.getLogger(__name__)


class SuperuserAuthHandler(BearerAuthHandler):
    """
    A FastAPI dependency for superuser authentication.

    Validates that the token matches the configured superuser token
    and returns the superuser identity from configuration.
    """

    async def __call__(
        self, request: Request, bearer_token: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> UserIdentity:
        token_str = bearer_token.credentials
        return await self.authenticate_token(token_str, request)

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates the superuser using the configured token.

        Superuser operates within a virtual "superuser tenant" that has full admin access
        (aihub.admin.>), effectively bypassing tenant restrictions while still going through
        the two-stage access control system.
        """
        if not token_str:
            raise HTTPException(status_code=401, detail="Token missing.")

        settings = SuperuserSettings()
        if token_str != settings.TOKEN.get_secret_value():
            raise HTTPException(status_code=401, detail="Invalid token.")

        # Create virtual superuser tenant with full admin access
        # This bypasses tenant restrictions while still going through access control
        virtual_superuser_tenant = TenantIdentity(
            id="__superuser_tenant__",
            name="Superuser",
            access_rules=["aihub.admin.>"],
        )

        # Construct UserIdentity here (instead of in SuperuserSettings) to avoid circular import
        return UserIdentity(
            name=settings.NAME,  # type: ignore[arg-type]
            email=settings.EMAIL,  # type: ignore[arg-type]
            id=settings.OID,  # type: ignore[arg-type]
            roles=settings.ROLES,
            acting_within_tenant=virtual_superuser_tenant,
        )
