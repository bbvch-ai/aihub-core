import logging

import jwt
from fastapi import HTTPException, Request, Security

from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.auth.identity.sys_admin_identity import SysAdminIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.auth.roles import SYS_ADMIN_ROLE

logger = logging.getLogger(__name__)


class SysAdminAuthHandler:
    """Authenticates system administrators by validating their JWT and checking for the AIHubSysAdmin realm role.

    This is a standalone FastAPI dependency (not extending AuthHandler) because it returns
    SysAdminIdentity instead of UserIdentity — sysadmin operations are outside tenant context.
    Reuses KeycloakAuthHandler's JWKS caching for efficient key resolution.
    """

    def __init__(self) -> None:
        self._keycloak = KeycloakAuthHandler()
        self._config = self._keycloak.config

    async def __call__(
        self,
        request: Request,
        oauth_token: str = Security(KeycloakSettings().SCHEMA),
    ) -> SysAdminIdentity:
        try:
            unverified_header = jwt.get_unverified_header(oauth_token)
            kid = unverified_header.get("kid")

            if not kid:
                raise HTTPException(status_code=401, detail="Invalid token format")

            rsa_key = await self._keycloak._get_rsa_key(kid)
            if not rsa_key:
                raise HTTPException(status_code=401, detail="Token verification failed")

            decoded_token = jwt.decode(
                oauth_token,
                rsa_key,
                algorithms=["RS256"],
                audience="account",
                issuer=self._config.ISSUER_URL,
            )

            sub = decoded_token.get("sub")
            if not sub:
                raise HTTPException(status_code=401, detail="Invalid token claims")

            roles = decoded_token.get("roles", [])
            if SYS_ADMIN_ROLE not in roles:
                logger.warning(
                    "User %s attempted sysadmin access without %s role. Has roles: %s",
                    decoded_token.get("email", "unknown"),
                    SYS_ADMIN_ROLE,
                    roles,
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: Requires the {SYS_ADMIN_ROLE} role.",
                )

            return SysAdminIdentity(
                id=sub,
                name=decoded_token.get("name", decoded_token.get("preferred_username", "")),
                email=decoded_token.get("email", ""),
            )

        except HTTPException:
            raise
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token verification failed: Invalid token")
        except Exception as e:
            logger.exception("Unexpected error during sysadmin token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication error")
