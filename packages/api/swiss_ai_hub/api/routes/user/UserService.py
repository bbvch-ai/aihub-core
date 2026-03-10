from typing import TYPE_CHECKING

from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.identity.TenantIdentity import TenantIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.UserEntity import UserEntity

from swiss_ai_hub.api.routes.user.dto.UserDTO import UserDTO
from swiss_ai_hub.api.routes.user.dto.UserWithAccessDTO import UserWithAccessDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners.Runner import Runner


class UserService:
    """Admin-level user management: listing and retrieving users within a tenant."""

    @staticmethod
    async def get_user_by_oid(user_oid: str) -> UserDTO:
        user_entity = UserEntity.by_oid(user_oid)
        return UserDTO.from_user_entity(user_entity)

    @staticmethod
    async def get_user_with_access_by_oid(
        user_oid: str, tenant: TenantIdentity, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> UserWithAccessDTO:
        """
        Retrieve a user with their access rules (which services, agents, and processes they can access).
        Access is calculated within the requesting user's tenant context.

        Raises DoesNotExist if the user is not found or does not belong to the given tenant.
        """
        tenant_user_ids = UserTenantRoleEntity.get_user_ids_in_tenant(tenant.id)
        if user_oid not in tenant_user_ids:
            raise DoesNotExist(f"User {user_oid} not found in tenant")
        user_entity = UserEntity.by_oid(user_oid)
        return await UserWithAccessDTO.from_user_entity(user_entity, tenant, runner, nc, t)

    @staticmethod
    async def get_paginated_users(tenant_id: str, page: int = 1, page_size: int = 20) -> tuple[int, list[UserDTO]]:
        """Retrieves a paginated list of users belonging to the given tenant."""
        tenant_user_ids = UserTenantRoleEntity.get_user_ids_in_tenant(tenant_id)
        skip = (page - 1) * page_size
        total = UserEntity.count_users(user_ids=tenant_user_ids)
        user_entities = UserEntity.get_paginated_users(skip=skip, limit=page_size, user_ids=tenant_user_ids)

        user_dtos = [UserDTO.from_user_entity(user) for user in user_entities]

        return total, user_dtos
