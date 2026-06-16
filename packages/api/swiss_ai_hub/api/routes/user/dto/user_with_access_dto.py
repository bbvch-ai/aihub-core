from typing import TYPE_CHECKING, Annotated, Self

from nats.aio.client import Client as NATS
from pydantic import Field
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity

from swiss_ai_hub.api.routes.access.access_catalog_service import AccessCatalogService
from swiss_ai_hub.api.routes.access.dto.access_dto import Access
from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.user_dto import UserDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class UserWithAccessDTO(UserDTO):
    access: Annotated[Access, Field(description="User access levels")]
    access_rules: Annotated[
        list[str],
        Field(description="The user's resolved access rules (union of their roles), to drive the capability view."),
    ]

    @classmethod
    async def from_user_identity(
        cls, user: UserIdentity, tenant: TenantIdentity, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> Self:
        dashboard = UserDashboardEntity.get_dashboard(user.id) or UserDashboardEntity.create_default_dashboard()
        dashboard_dto = DashboardDTO(**dashboard.to_mongo())

        user_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user.id, tenant.id)
        valid_roles = RoleEntity.filter_existing_roles(user_roles, tenant.id)

        access_checker = AccessChecker.from_user(user)
        access = await AccessCatalogService.build_access(access_checker, runner, t, include_denied=False)

        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=None,
            dashboard=dashboard_dto,
            roles=valid_roles,
            is_sys_admin=user.is_sys_admin,
            access=access,
            access_rules=sorted(access_checker.access_rules),
        )
