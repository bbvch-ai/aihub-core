from typing import TYPE_CHECKING, Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.user.UserEntity import UserEntity
from nats.aio.client import Client as NATS
from pydantic import BaseModel, Field

from aihub_api.routes.user.dto.Dashboard.DashboardDTO import DashboardDTO
from aihub_api.routes.user.dto.UserDTO import UserDTO

if TYPE_CHECKING:
    from aihub_lib.runners.Runner import Runner


class UserAccess(BaseModel):
    name: Annotated[str, Field(description="Name of the service/agent/process to which user has access to")]
    level: Annotated[AccessLevel, Field(description="Users access level to service/agent/process")]


class Access(BaseModel):
    services: Annotated[list[UserAccess], Field(description="List of services and access levels")] = []
    agents: Annotated[list[UserAccess], Field(description="List of agents and access levels")] = []
    processes: Annotated[list[UserAccess], Field(description="List of processes and access levels")] = []


class UserWithAccessDTO(UserDTO):
    access: Annotated[Access, Field(description="User access levels")]

    @classmethod
    async def from_user_entity(cls, user_entity: UserEntity, runner: "Runner", nc: NATS, t: LocaleHandler):
        from aihub_api.routes.agent.AgentService import AgentService
        from aihub_api.routes.process.ProcessService import ProcessService

        dashboard_data = user_entity.dashboard.to_mongo()
        dashboard_dto = DashboardDTO(**dashboard_data)
        roles = user_entity.get_roles()
        valid_roles = RoleEntity.filter_existing_roles(roles)

        access_rules = RoleEntity.get_access_rules_for_roles(roles)

        access_checker = AccessChecker(list(access_rules))
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
            id=user_entity.id,
            name=user_entity.name,
            email=user_entity.email,
            profile_image=user_entity.profile_image,
            dashboard=dashboard_dto,
            favorite_modules=user_entity.favorite_modules,
            roles=valid_roles,
            last_accessed=user_entity.last_updated,
            access=access,
        )
