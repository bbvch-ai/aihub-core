from typing import TYPE_CHECKING

from fastapi import HTTPException
from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity

from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.user_dto import UserDTO
from swiss_ai_hub.api.routes.user.dto.user_with_access_dto import UserWithAccessDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class UserService:
    """Admin-level user management: listing and retrieving users within a tenant."""

    @staticmethod
    async def get_user_by_oid(user_oid: str) -> UserDTO:
        keycloak_user = await KeycloakAdminService.get_user_by_id(user_oid)
        dashboard = UserDashboardEntity.get_dashboard(user_oid)
        dashboard_dto = DashboardDTO(**dashboard.to_mongo()) if dashboard else None
        return UserDTO.from_keycloak_user_with_dashboard(keycloak_user, dashboard_dto)

    @staticmethod
    async def get_user_with_access_by_oid(
        user_oid: str, tenant: TenantIdentity, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> UserWithAccessDTO:
        """
        Retrieve a user with their access rules (which services, agents, and processes they can access).
        Access is calculated within the requesting user's tenant context.

        Raises DoesNotExist if the user is not found or does not belong to the given tenant.
        """
        if not await KeycloakAdminService.is_user_member_of_tenant(user_oid, tenant.id):
            raise DoesNotExist(f"User {user_oid} not found in tenant")
        keycloak_user = await KeycloakAdminService.get_user_by_id(user_oid)
        sys_admin_ids = await KeycloakAdminService.get_user_ids_with_realm_role(SYS_ADMIN_ROLE)
        user_identity = UserIdentity(
            id=user_oid,
            name=keycloak_user.name,
            email=keycloak_user.email,
            roles=UserTenantRoleEntity.get_roles_for_user_in_tenant(user_oid, tenant.id),
            acting_within_tenant=tenant,
            is_sys_admin=user_oid in sys_admin_ids,
        )
        return await UserWithAccessDTO.from_user_identity(user_identity, tenant, runner, nc, t)

    @staticmethod
    async def get_paginated_users(tenant_id: str, page: int = 1, page_size: int = 20) -> tuple[int, list[UserDTO]]:
        """Retrieves a paginated list of users belonging to the given tenant.

        Existence is validated against Keycloak (source of truth); a missing or
        orphaned tenant results in a 404 rather than a silent empty page.
        """

        if not await KeycloakAdminService.tenant_exists(tenant_id):
            raise HTTPException(status_code=404, detail="Tenant not found.")

        skip = (page - 1) * page_size
        members = await KeycloakAdminService.get_tenant_members(tenant_id, offset=skip, limit=page_size)
        total = await KeycloakAdminService.count_tenant_members(tenant_id)

        member_ids = [m.id for m in members]
        roles_by_user = UserTenantRoleEntity.get_roles_map_for_users_in_tenant(member_ids, tenant_id)
        sys_admin_ids = await KeycloakAdminService.get_user_ids_with_realm_role(SYS_ADMIN_ROLE)

        user_dtos = [
            UserDTO.from_keycloak_user_with_dashboard(
                m,
                None,
                roles=roles_by_user.get(m.id, []),
                is_sys_admin=m.id in sys_admin_ids,
            )
            for m in members
        ]
        return total, user_dtos
