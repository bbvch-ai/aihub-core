import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

logger = logging.getLogger(__name__)


class AuthHandler(ABC):
    """
    Base class for authentication handlers.

    Authentication handlers validate credentials and return user identities.
    """

    @abstractmethod
    async def __call__(self, request: Request) -> UserIdentity:
        """
        Given a FastAPI Request, this method must either return an UserIdentity or raise an HTTPException.
        """
        pass

    ACTIVE_TENANT_SLUG = "active"

    @abstractmethod
    async def authenticate_token(self, token: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates a user based on a token string.

        When a request is provided, the tenant is resolved from the tenant_id path parameter.
        Without a request (e.g., WebSocket connections), falls back to the user's active tenant.
        """
        pass

    @staticmethod
    async def _resolve_active_tenant(user_id: str) -> TenantMetadataEntity | None:
        """Resolves the user's active tenant.

        Keycloak is the sole source of truth for tenant existence, membership, and
        the active-tenant attribute; the metadata collection is only consulted for
        display fields. If the Keycloak group is gone or the user is not a member
        of the group, the active tenant is cleared and the caller must pick a new
        one. Membership is orthogonal to ``AIHubSysAdmin`` — the superuser passes
        every membership check by virtue of being explicitly added to every tenant
        group (not by virtue of any role).

        **HTTP status choice — 400, not 403 (contrast with ``_resolve_tenant_by_id``):**
        This path resolves the caller's *own* stored active-tenant attribute. If it
        no longer resolves, the caller already knew the id — there is nothing to
        leak by telling them so. A 400 with an actionable "please select a new
        tenant" message is the correct UX; a 403 here would be misleading (it is
        not that they lack access, it is that their pinned context went stale).
        """
        active_tenant_id = await KeycloakAdminService.get_active_tenant_id(user_id)
        if not active_tenant_id:
            return None

        if not await KeycloakAdminService.tenant_exists(active_tenant_id):
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(
                status_code=400,
                detail="Your active tenant is no longer accessible. Please select a new tenant.",
            )

        if not await KeycloakAdminService.is_user_member_of_tenant(user_id, active_tenant_id):
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(
                status_code=400,
                detail="Your active tenant is no longer accessible. Please select a new tenant.",
            )

        tenant = TenantMetadataEntity.get_metadata_by_tenant_id(active_tenant_id)
        if not tenant:
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(
                status_code=400,
                detail="Your active tenant is no longer accessible. Please select a new tenant.",
            )

        return tenant

    @staticmethod
    async def _resolve_tenant_by_id(tenant_id: str, user_id: str) -> TenantIdentity:
        """Resolves a tenant requested via URL path param.

        Existence and membership are both validated against Keycloak. The metadata
        collection is then consulted for the display name. Failures surface as a
        uniform 403 "Access denied" to avoid leaking which tenants exist — all
        three rejection branches (tenant absent from Keycloak, user not a member,
        metadata row missing) return the same response so an attacker probing
        ``/api/v1/{tenant_id}/...`` cannot enumerate tenants or distinguish
        "doesn't exist" from "not my tenant". Server-side logs differentiate the
        three cases for operators. Membership is checked uniformly for every
        user — the superuser passes because they are a member of every tenant
        group, not because of the ``AIHubSysAdmin`` role.

        **HTTP status choice — 403, not 400 (contrast with ``_resolve_active_tenant``):**
        the tenant id here is attacker-controlled input from the URL, not the
        caller's own stored context, so the enumeration concern dominates UX.
        """
        if not await KeycloakAdminService.tenant_exists(tenant_id):
            logger.warning(f"Tenant {tenant_id} not found in Keycloak during resolution for user {user_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        if not await KeycloakAdminService.is_user_member_of_tenant(user_id, tenant_id):
            logger.warning(f"User {user_id} attempted to access tenant {tenant_id} without membership")
            raise HTTPException(status_code=403, detail="Access denied")

        tenant_entity = TenantMetadataEntity.get_metadata_by_tenant_id(tenant_id)
        if not tenant_entity:
            logger.warning(f"Tenant {tenant_id} exists in Keycloak but has no metadata")
            raise HTTPException(status_code=403, detail="Access denied")

        return TenantIdentity.from_tenant_metadata_entity(tenant_entity)

    @staticmethod
    def has_tenant_in_request(request: Request) -> bool:
        """Whether the request targets a tenant-scoped route (has ``{tenant_id}`` in the path)."""
        return "tenant_id" in request.path_params

    @staticmethod
    async def resolve_tenant_for_user(request: Request, user_id: str) -> TenantIdentity:
        tenant_id = request.path_params.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Missing tenant context")

        if tenant_id == AuthHandler.ACTIVE_TENANT_SLUG:
            active_tenant = await AuthHandler._resolve_active_tenant(user_id)
            if active_tenant:
                return TenantIdentity.from_tenant_metadata_entity(active_tenant)
            raise HTTPException(
                status_code=400,
                detail="No active tenant set. Please select a tenant first.",
            )

        return await AuthHandler._resolve_tenant_by_id(tenant_id, user_id)

    @staticmethod
    async def get_active_tenant_for_user(user_id: str) -> TenantIdentity:
        active_tenant = await AuthHandler._resolve_active_tenant(user_id)
        if active_tenant:
            return TenantIdentity.from_tenant_metadata_entity(active_tenant)
        raise HTTPException(
            status_code=400,
            detail="No active tenant set. Please select a tenant first.",
        )

    async def build_identity(
        self,
        *,
        user_id: str,
        name: str,
        email: str,
        request: Request | None,
        is_sys_admin: bool = False,
    ) -> UserIdentity:
        """Builds a UserIdentity with tenant context resolved from the request or active tenant fallback.

        ``is_sys_admin`` flows through to ``UserIdentity`` so the permission layer
        (``AccessChecker``) can grant admin-level access within tenants the user is
        actually a member of. It is NOT used to decide membership.
        """
        if request and self.has_tenant_in_request(request):
            tenant = await self.resolve_tenant_for_user(request, user_id)
        else:
            tenant = await self.get_active_tenant_for_user(user_id)
        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
        return UserIdentity(
            id=user_id,
            name=name,
            email=email,
            roles=roles,
            acting_within_tenant=tenant,
            is_sys_admin=is_sys_admin,
        )
