import logging

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.no_auth.NoAuthConfig import NoAuthConfig

logger = logging.getLogger(__name__)


async def use_no_auth_user() -> AuthenticatedUser:
    """
    A FastAPI dependency that returns a static, pre-configured user for testing or local development.

    ### Why use_no_auth_user?
    In some cases, you may want to bypass authentication entirely, either because you're:
    - Running locally without an identity provider.
    - Writing integration tests that don't require real authentication.
    - Quickly prototyping new features.

    This function:
    - Logs a warning to remind you it's not suitable for production.
    - Returns an `AuthenticatedUser` populated with values from `NoAuthConfig`.

    By using environment variables or a `.env` file, you can simulate different user identities and roles
    without any OAuth tokens or external services.
    """

    logger.warning("You are using the use_no_auth_user function. This is not recommended for production use.")
    config = NoAuthConfig()
    return AuthenticatedUser(
        name=config.NAME,
        preferred_username=config.EMAIL,
        oid=str(config.OID),
        roles=config.ROLES,
    )
