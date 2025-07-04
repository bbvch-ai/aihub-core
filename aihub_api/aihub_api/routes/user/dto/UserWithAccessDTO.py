from typing import TYPE_CHECKING, Annotated, List

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
    name: Annotated[str, Field(description="Name of the service")]
    level: Annotated[AccessLevel, Field(description="Name of the service")]


class Access(BaseModel):
    services: Annotated[List[UserAccess], Field(description="List of services and access levels")] = []
    agents: Annotated[List[UserAccess], Field(description="List of agents and access levels")] = []
    processes: Annotated[List[UserAccess], Field(description="List of processes and access levels")] = []


class UserWithAccessDTO(UserDTO):
    access: Annotated[Access, Field(description="User access levels")]

    @classmethod
    async def from_user_entity(cls, user_entity: UserEntity, runner: "Runner", nc: NATS, t: LocaleHandler):
        from aihub_api.routes.agent.AgentService import AgentService

        dashboard_data = user_entity.dashboard.to_mongo()
        dashboard_dto = DashboardDTO(**dashboard_data)
        valid_roles = RoleEntity.filter_existing_roles(user_entity.roles)

        access_rules = RoleEntity.get_access_rules_for_roles(user_entity.roles)

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

        agents = await AgentService.get_agents(nc, t)
        for agent in agents:
            agent_access = access_checker.access_level_for_agent(agent_class=agent.agent_class, agent_id=agent.agent_id)
            if agent_access == AccessLevel.ACCESS_DENIED:
                continue

            access.agents.append(UserAccess(name=agent.agent_config.name, level=agent_access))

        # TODO: Add processes

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
