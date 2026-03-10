import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.identity.TenantIdentity import TenantIdentity
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.persistence.access.entities.TenantEntity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

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
        Without a request (e.g., WebSocket connections), falls back to the default tenant.
        """
        pass

    @staticmethod
    def resolve_tenant_for_user(request: Request, user_id: str) -> TenantIdentity:
        """
        Resolve tenant context from request headers and verify user membership.

        Extracts the x-tenant-id header and verifies the user has access to that tenant.
        Falls back to the default tenant if no header is provided.
        """
        tenant_id = request.headers.get("x-tenant-id")

        if not tenant_id:
            logger.debug("No x-tenant-id header found, falling back to default tenant")
            tenant_entity = TenantEntity.get_default_tenant()
            if not tenant_entity:
                raise HTTPException(
                    status_code=500,
                    detail="No default tenant configured and no x-tenant-id header provided",
                )
        else:
            tenant_entity = TenantEntity.get_tenant_by_id(tenant_id)
            if not tenant_entity:
                logger.warning(f"Tenant {tenant_id} not found during resolution for user {user_id}")
                raise HTTPException(status_code=403, detail="Access denied")

        # Verify user has access to this tenant
        tenant_id_str = str(tenant_entity.id)
        user_roles_in_tenant = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant_id_str)
        if not user_roles_in_tenant:
            logger.warning(f"User {user_id} attempted to access tenant {tenant_id_str} without membership")
            raise HTTPException(status_code=403, detail="Access denied")

        return TenantIdentity.from_tenant_entity(tenant_entity)

    @staticmethod
    def get_default_tenant_for_user(user_id: str) -> TenantIdentity:
        """
        Get the default tenant for a user and verify membership.

        Used for contexts without a request object (e.g., WebSocket connections).
        """
        default_tenant = TenantEntity.get_default_tenant()
        if not default_tenant:
            raise HTTPException(status_code=500, detail="Default tenant not configured")

        # Verify user has access to default tenant
        user_roles_in_tenant = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, str(default_tenant.id))
        if not user_roles_in_tenant:
            logger.warning(f"User {user_id} does not have access to default tenant")
            raise HTTPException(status_code=403, detail="Access denied")

        return TenantIdentity.from_tenant_entity(default_tenant)
