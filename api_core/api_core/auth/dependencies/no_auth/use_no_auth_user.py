import logging

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.auth.dependencies.no_auth.NoAuthConfig import NoAuthConfig

logger = logging.getLogger(__name__)

async def use_no_auth_user() -> AuthenticatedUser:
    logger.warning(f"You are using the use_no_auth_user function. This is not recommended for production use.")
    return AuthenticatedUser(
        name=NoAuthConfig().NAME,
        preferred_username=NoAuthConfig().EMAIL,
        oid=str(NoAuthConfig().OID),
        roles=NoAuthConfig().ROLES,
    )

