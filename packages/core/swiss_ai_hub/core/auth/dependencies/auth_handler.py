import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
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
    async def _resolve_active_tenant(user_id: str) -> TenantEntity | None:
        active_tenant_id = await KeycloakAdminService.get_active_tenant_id(user_id)
        if not active_tenant_id:
            return None

        tenant = TenantEntity.get_tenant_by_id(active_tenant_id)
        if not tenant:
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(
                status_code=400,
                detail="Your active tenant is no longer accessible. Please select a new tenant.",
            )

        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
        if not roles:
            await KeycloakAdminService.clear_active_tenant(user_id)
            raise HTTPException(
                status_code=400,
                detail="Your active tenant is no longer accessible. Please select a new tenant.",
            )

        return tenant

    @staticmethod
    def _resolve_tenant_by_id(tenant_id: str, user_id: str) -> TenantIdentity:
        tenant_entity = TenantEntity.get_tenant_by_id(tenant_id)
        if not tenant_entity:
            logger.warning(f"Tenant {tenant_id} not found during resolution for user {user_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        tenant_id_str = str(tenant_entity.id)
        user_roles_in_tenant = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id_str)
        if not user_roles_in_tenant:
            logger.warning(f"User {user_id} attempted to access tenant {tenant_id_str} without membership")
            raise HTTPException(status_code=403, detail="Access denied")

        return TenantIdentity.from_tenant_entity(tenant_entity)

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
                return TenantIdentity.from_tenant_entity(active_tenant)
            raise HTTPException(
                status_code=400,
                detail="No active tenant set. Please select a tenant first.",
            )

        return AuthHandler._resolve_tenant_by_id(tenant_id, user_id)

    @staticmethod
    async def get_active_tenant_for_user(user_id: str) -> TenantIdentity:
        active_tenant = await AuthHandler._resolve_active_tenant(user_id)
        if active_tenant:
            return TenantIdentity.from_tenant_entity(active_tenant)
        raise HTTPException(
            status_code=400,
            detail="No active tenant set. Please select a tenant first.",
        )

    async def build_identity(self, *, user_id: str, name: str, email: str, request: Request | None) -> UserIdentity:
        """Builds a UserIdentity with tenant context resolved from the request or active tenant fallback."""
        if request and self.has_tenant_in_request(request):
            tenant = await self.resolve_tenant_for_user(request, user_id)
            roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
            return UserIdentity(id=user_id, name=name, email=email, roles=roles, acting_within_tenant=tenant)
        elif request:
            return UserIdentity(id=user_id, name=name, email=email, roles=[])
        else:
            tenant = await self.get_active_tenant_for_user(user_id)
            roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)
            return UserIdentity(id=user_id, name=name, email=email, roles=roles, acting_within_tenant=tenant)
