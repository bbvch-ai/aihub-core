import logging
from typing import Any

import httpx
import jwt
from cachetools import TTLCache
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from fastapi import HTTPException, Request, Security
from jwt.algorithms import RSAAlgorithm

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.infrastructure.api.default_tenant_settings import DefaultTenantSettings
from swiss_ai_hub.core.infrastructure.api.user_signup_settings import UserSignupSettings
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class KeycloakAuthHandler(AuthHandler):
    """
    A FastAPI dependency for Keycloak OIDC authentication.

    Validates JWT tokens using JWKS from Keycloak. User data is extracted
    directly from JWT claims - no external API calls needed after JWKS fetch.
    """

    _jwks_cache: TTLCache[str, dict[str, Any]] = TTLCache(maxsize=100, ttl=21600)  # 6 hour cache
    _rsa_key_cache: TTLCache[str, RSAPublicKey | RSAPrivateKey] = TTLCache(maxsize=10, ttl=21600)

    def __init__(self) -> None:
        self.config = KeycloakSettings()

    async def __call__(self, request: Request, oauth_token: str = Security(KeycloakSettings().SCHEMA)) -> UserIdentity:
        return await self.authenticate_token(oauth_token, request)

    async def _get_jwks(self) -> dict[str, Any]:
        """Retrieves the JWKS from Keycloak, using caching to minimize API calls."""
        cache_key = "jwks"
        if cache_key in self._jwks_cache:
            return self._jwks_cache[cache_key]

        try:
            logger.debug("JWKS cache miss, fetching from %s", self.config.JWKS_URL)
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=30.0, read=10.0)) as client:
                jwks_response = await client.get(self.config.JWKS_URL)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
                self._jwks_cache[cache_key] = jwks
                return jwks
        except httpx.HTTPError as e:
            logger.exception("Error fetching JWKS: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication service unavailable")

    async def _get_rsa_key(self, kid: str) -> RSAPublicKey | RSAPrivateKey | None:
        """Gets an RSA key for the specified key ID (kid)."""
        if kid in self._rsa_key_cache:
            return self._rsa_key_cache[kid]

        jwks = await self._get_jwks()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                rsa_key = RSAAlgorithm.from_jwk(key)
                self._rsa_key_cache[kid] = rsa_key
                return rsa_key

        return None

    async def authenticate_token(self, oauth_token: str, request: Request | None = None) -> UserIdentity:
        """Authenticates a user using a Keycloak JWT token."""
        try:
            unverified_header = jwt.get_unverified_header(oauth_token)
            kid = unverified_header.get("kid")

            if not kid:
                logger.warning("Token missing kid in header")
                raise HTTPException(status_code=401, detail="Invalid token format")

            rsa_key = await self._get_rsa_key(kid)

            if not rsa_key:
                logger.warning("No matching key found for kid: %s", kid)
                raise HTTPException(status_code=401, detail="Token verification failed")

            decoded_token = jwt.decode(
                oauth_token,
                rsa_key,
                algorithms=["RS256"],
                audience="account",
                issuer=self.config.ISSUER_URL,
            )

            logger.debug("Decoded token claims: %s", list(decoded_token.keys()))

            sub = decoded_token.get("sub")
            name = decoded_token.get("name", decoded_token.get("preferred_username", ""))
            email = decoded_token.get("email", "")

            if not sub:
                logger.warning("Token missing sub claim. Available claims: %s", list(decoded_token.keys()))
                raise HTTPException(status_code=401, detail="Invalid token claims")

            realm_roles = decoded_token.get("roles", [])
            is_sys_admin = SYS_ADMIN_ROLE in realm_roles

            # Sync tenant memberships from JWT tenants claim
            tenants_claim = decoded_token.get("tenants", [])
            self._sync_tenant_memberships(sub, tenants_claim)
            await self._ensure_active_tenant(sub)

            return await self.build_identity(
                user_id=sub,
                name=name,
                email=email,
                request=request,
                is_sys_admin=is_sys_admin,
            )

        except HTTPException:
            raise
        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", str(e))
            raise HTTPException(status_code=401, detail="Token verification failed: Invalid token")
        except httpx.HTTPError:
            logger.exception("HTTP error during token validation")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
        except Exception as e:
            logger.exception("Unexpected error during token validation: %s", str(e))
            raise HTTPException(status_code=500, detail="Authentication error")

    @staticmethod
    def _extract_tenant_ids_from_claim(tenants_claim: list[str]) -> list[str]:
        """Parses the JWT `tenants` claim into a list of tenant IDs.

        The claim contains Keycloak group paths like `/tenants/<tenant-id>`. Only entries
        under the `/tenants/` parent are considered.
        """
        return [path.split("/")[-1] for path in tenants_claim if path.startswith("/tenants/")]

    @staticmethod
    def _needs_membership_sync(user_id: str, tenant_ids: list[str]) -> bool:
        """Fast path: returns False if the user already has memberships for all tenants in the claim."""
        db_tenant_ids = set(UserTenantRoleEntity.get_tenant_ids_for_user(user_id))
        return not set(tenant_ids).issubset(db_tenant_ids)

    @staticmethod
    def _resolve_roles_for_new_member(tenant_id: str) -> list[str]:
        """Returns the roles to assign when creating a new user-tenant association.

        The first user to join a tenant gets admin roles; subsequent users get
        regular roles. The seeded superuser is the natural first admin when
        they log in during initial platform setup.
        """
        settings = UserSignupSettings()
        existing_user_ids = UserTenantRoleEntity.get_user_ids_in_tenant(tenant_id)
        if not existing_user_ids:
            logger.info("First user signup in tenant %s, assigning admin roles", tenant_id)
            return settings.first_admin_user_roles_list
        return settings.regular_user_roles_list

    @staticmethod
    def _ensure_membership_for_tenant(user_id: str, tenant_id: str) -> None:
        """Creates a `UserTenantRoleEntity` for the user in the given tenant if missing.

        The tenant_id originates from the JWT ``tenants`` claim, which is issued by
        Keycloak itself — Keycloak is therefore the source of truth that this
        membership is legitimate, regardless of whether MongoDB metadata exists
        for the tenant. Skips silently only if the membership already has roles.
        """
        if UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id):
            return

        if not TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id):
            logger.info(
                "Tenant '%s' from JWT claim has no metadata yet; membership created without display data",
                tenant_id,
            )

        roles_to_assign = KeycloakAuthHandler._resolve_roles_for_new_member(tenant_id)
        UserTenantRoleEntity.create_or_update(user_id=user_id, tenant_id=tenant_id, roles=roles_to_assign)
        logger.info(
            "Created tenant association for user %s in tenant %s with roles: %s",
            user_id,
            tenant_id,
            roles_to_assign,
        )

    @staticmethod
    def _sync_tenant_memberships(user_id: str, tenants_claim: list[str]) -> None:
        """Syncs tenant memberships from the JWT `tenants` claim to `UserTenantRoleEntity`.

        Fast path: if the user's existing memberships already cover all tenants in the JWT
        claim, skip the sync entirely. New tenants added to the user's Keycloak groups are
        picked up on the next request. Removals are not propagated (would require explicit
        cleanup).
        """
        tenant_ids = KeycloakAuthHandler._extract_tenant_ids_from_claim(tenants_claim)
        if not tenant_ids:
            return

        if not KeycloakAuthHandler._needs_membership_sync(user_id, tenant_ids):
            return

        for tenant_id in tenant_ids:
            KeycloakAuthHandler._ensure_membership_for_tenant(user_id, tenant_id)

    @staticmethod
    async def _ensure_active_tenant(user_id: str) -> None:
        """Ensures the user has a valid active tenant, auto-selecting one if needed.

        Keycloak is the sole source of truth for tenant membership; the candidate
        set is exactly the groups the user belongs to in Keycloak. The superuser
        naturally has every tenant available because they are explicitly added to
        every tenant group on creation — no sysadmin short-circuit.

        Selection order when no valid active tenant is set:
        1. The user's only tenant, if they have exactly one membership.
        2. The configured default tenant (``AIHUB_DEFAULT_TENANT_ID``) if the user is a member.
        3. The earliest-created tenant (by metadata timestamp) among the user's memberships.
        """
        existing_tenant_ids = await KeycloakAdminService.get_user_tenant_ids(user_id)
        if not existing_tenant_ids:
            return

        current = await KeycloakAdminService.get_active_tenant_id(user_id)
        if current and current in existing_tenant_ids:
            return

        default_id = DefaultTenantSettings().ID
        if len(existing_tenant_ids) == 1:
            selected_id = next(iter(existing_tenant_ids))
        elif default_id in existing_tenant_ids:
            selected_id = default_id
        else:
            earliest = TenantMetadataEntity.objects(id__in=list(existing_tenant_ids)).order_by("created_at").first()
            if earliest:
                selected_id = earliest.id
            else:
                selected_id = sorted(existing_tenant_ids)[0]

        await KeycloakAdminService.set_active_tenant(user_id, selected_id)
        logger.info("Auto-selected active tenant %s for user %s", selected_id, user_id)
