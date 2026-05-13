from typing import TYPE_CHECKING, Annotated, Self

from nats.aio.client import Client as NATS
from pydantic import BaseModel, Field
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity

from swiss_ai_hub.api.routes.user.dto.dashboard.dashboard_dto import DashboardDTO
from swiss_ai_hub.api.routes.user.dto.user_dto import UserDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners import Runner


class UserAccess(BaseModel):
    name: Annotated[str, Field(description="Name of the service/agent/process to which user has access to")]
    level: Annotated[AccessLevel, Field(description="Users access level to service/agent/process")]


class Access(BaseModel):
    services: Annotated[list[UserAccess], Field(description="List of services and access levels")] = []
    agents: Annotated[list[UserAccess], Field(description="List of agents and access levels")] = []
    processes: Annotated[list[UserAccess], Field(description="List of processes and access levels")] = []


class UserWithAccessDTO(UserDTO):
    access: Annotated[Access, Field(description="User access levels")]
    preferred_locale: Annotated[
        str | None,
        Field(description="The user's persisted UI language, or null if not yet set."),
    ] = None

    @classmethod
    async def from_user_identity(
        cls, user: UserIdentity, tenant: TenantIdentity, runner: "Runner", nc: NATS, t: LocaleHandler
    ) -> Self:
        from swiss_ai_hub.api.routes.agent.agent_service import AgentService
        from swiss_ai_hub.api.routes.process.process_service import ProcessService

        dashboard = UserDashboardEntity.get_dashboard(user.id) or UserDashboardEntity.create_default_dashboard()
        dashboard_dto = DashboardDTO(**dashboard.to_mongo())

        user_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user.id, tenant.id)
        valid_roles = RoleEntity.filter_existing_roles(user_roles, tenant.id)

        access_checker = AccessChecker.from_user(user)
        access = Access()

        for controller in runner.controllers:
            user_service_access = access_checker.access_level_for_service(controller.service_name)
            if user_service_access == AccessLevel.ACCESS_DENIED:
                continue

            if controller.additionally_required_permission:
                user_special_access = access_checker.access_level(controller.additionally_required_permission)
                if user_special_access == AccessLevel.ACCESS_DENIED:
                    continue

            access.services.append(UserAccess(name=t.extract(controller.name), level=user_service_access))

        agent_instances = await AgentService.get_all_agent_instances(t)
        for agent_instance in agent_instances:
            agent_access = access_checker.access_level_for_agent(
                agent_class=agent_instance.agent_class, agent_id=agent_instance.agent_id
            )
            if agent_access == AccessLevel.ACCESS_DENIED:
                continue

            access.agents.append(UserAccess(name=agent_instance.name, level=agent_access))

        processes = await ProcessService.get_all_process_instances(t)
        for process in processes:
            process_access = access_checker.access_level_for_process(
                process_class=process.process_class, process_id=process.process_id
            )
            if process_access == AccessLevel.ACCESS_DENIED:
                continue

            access.processes.append(UserAccess(name=process.process_config.name, level=process_access))

        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            profile_image=None,
            dashboard=dashboard_dto,
            roles=valid_roles,
            is_sys_admin=user.is_sys_admin,
            access=access,
            preferred_locale=user.preferred_locale,
        )
