import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

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

    @abstractmethod
    async def authenticate_token(self, token: str, request: Request | None = None) -> UserIdentity:
        """
        Authenticates a user based on a token string.

        When a request is provided, the tenant is resolved from the x-tenant-id header.
        Without a request (e.g., WebSocket connections), falls back to the user's active tenant.
        """
        pass

    @staticmethod
    def _resolve_active_tenant(user_id: str) -> TenantEntity | None:
        """Attempts to resolve the user's persisted active tenant, returning None if invalid."""
        user = UserEntity.objects(id=user_id).only("active_tenant_id").first()
        if not user or not user.active_tenant_id:
            return None

        tenant = TenantEntity.get_tenant_by_id(user.active_tenant_id)
        if not tenant:
            UserEntity.objects(id=user_id).update(set__active_tenant_id=None)
            return None

        roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, str(tenant.id))
        if not roles:
            UserEntity.objects(id=user_id).update(set__active_tenant_id=None)
            return None

        return tenant

    @staticmethod
    def _fall_back_to_default_tenant(user_id: str) -> TenantEntity:
        """Returns the system default tenant, updating the user's active tenant to match."""
        default_tenant = TenantEntity.get_default_tenant()
        if not default_tenant:
            raise HTTPException(
                status_code=500,
                detail="No default tenant configured and no x-tenant-id header provided",
            )

        user_roles_in_tenant = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, str(default_tenant.id))
        if not user_roles_in_tenant:
            logger.warning(f"User {user_id} does not have access to default tenant")
            raise HTTPException(status_code=403, detail="Access denied")

        UserEntity.objects(id=user_id).update(set__active_tenant_id=str(default_tenant.id))
        return default_tenant

    ACTIVE_TENANT_SLUG = "active"

    @staticmethod
    def resolve_tenant_for_user(request: Request, user_id: str) -> TenantIdentity:
        """
        Resolve tenant context from the request path parameter and verify user membership.

        The tenant_id path parameter is required on all API routes. When set to "active",
        resolves to the user's persisted active tenant (then the system default).
        When set to a concrete tenant ID, validates membership and updates the active tenant.
        """
        tenant_id = request.path_params.get("tenant_id") or request.headers.get("x-tenant-id")

        if not tenant_id or tenant_id == AuthHandler.ACTIVE_TENANT_SLUG:
            logger.debug("Resolving active tenant for user %s", user_id)
            active_tenant = AuthHandler._resolve_active_tenant(user_id)
            tenant_entity = active_tenant if active_tenant else AuthHandler._fall_back_to_default_tenant(user_id)
            return TenantIdentity.from_tenant_entity(tenant_entity)

        tenant_entity = TenantEntity.get_tenant_by_id(tenant_id)
        if not tenant_entity:
            logger.warning(f"Tenant {tenant_id} not found during resolution for user {user_id}")
            raise HTTPException(status_code=403, detail="Access denied")

        tenant_id_str = str(tenant_entity.id)
        user_roles_in_tenant = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id_str)
        if not user_roles_in_tenant:
            logger.warning(f"User {user_id} attempted to access tenant {tenant_id_str} without membership")
            raise HTTPException(status_code=403, detail="Access denied")

        UserEntity.objects(id=user_id).update_one(set__active_tenant_id=tenant_id_str)

        return TenantIdentity.from_tenant_entity(tenant_entity)

    @staticmethod
    def get_active_tenant_for_user(user_id: str) -> TenantIdentity:
        """
        Get the active tenant for a user and verify membership.

        Used for contexts without a request object (e.g., WebSocket connections).
        Falls back to the system default tenant if no active tenant is set.
        """
        active_tenant = AuthHandler._resolve_active_tenant(user_id)
        tenant_entity = active_tenant if active_tenant else AuthHandler._fall_back_to_default_tenant(user_id)
        return TenantIdentity.from_tenant_entity(tenant_entity)
