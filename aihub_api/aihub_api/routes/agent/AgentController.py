from typing import Annotated, Self

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Query, Security

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.CreateAgentInstanceRequest import CreateAgentInstanceRequest
from aihub_api.routes.agent.dto.FullAgentInstanceDTO import FullAgentInstanceDTO
from aihub_api.routes.agent.dto.UpdateAgentInstanceDTO import UpdateAgentInstanceDTO
from aihub_api.routes.thread.dto.PaginatedThreadsResponse import PaginatedThreadsResponse


class AgentController(Controller):
    """
    A controller managing endpoints related to agents, including classes and instances.

    ### API Structure
    - Agent Classes: `/agents/classes` - Agent definitions/templates
    - Agent Instances: `/agents/classes/{agent_class}/instances` - Configured deployments
    - Cross-class instances: `/agents/instances` - All instances across classes
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.agent.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.agent.description")
    icon = "mage:robot"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this resource")

    def __init__(
        self, *, auth: AuthHandler, route: str = "/agents", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    # ==================== Agent Classes Endpoints ====================

    def get_agent_classes(self, route: str = "/classes") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_classes(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            online: Annotated[bool | None, Query(description="Filter by online status")] = None,
        ) -> list[AgentClassDTO]:
            """
            Retrieve all available agent classes.
            Use `?online=true` for online classes only, `?online=false` for offline only.
            """
            return await AgentService.get_agent_classes(t, online=online)

        return self

    def get_agent_class(self, route: str = "/classes/{agent_class}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_class(
            agent_class: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> AgentClassDTO:
            """
            Retrieve details for a specific agent class.
            """
            return await AgentService.get_agent_class(agent_class, t)

        return self

    def get_agent_class_instances(self, route: str = "/classes/{agent_class}/instances") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_class_instances(
            agent_class: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[FullAgentInstanceDTO]:
            """
            Retrieve all instances of a specific agent class.
            """
            instances = await AgentService.get_agent_class_instances(agent_class, t)
            return [
                instance
                for instance in instances
                if AccessChecker.from_user(user).has_access_to_agent(instance.agent_class, instance.agent_id)
            ]

        return self

    def create_agent_instance(self, route: str = "/classes/{agent_class}/instances") -> Self:
        from fastapi import status

        @self.router.post(route, tags=self.tags, status_code=status.HTTP_201_CREATED)
        async def create_agent_instance(
            agent_class: str,
            request: CreateAgentInstanceRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.{agent_class}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullAgentInstanceDTO:
            """
            Create a new agent instance from an existing agent class.
            """
            return await AgentService.create_agent_instance(agent_class, request, t)

        return self

    def get_agent_instance(self, route: str = "/classes/{agent_class}/instances/{agent_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_instance(
            agent_class: str,
            agent_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullAgentInstanceDTO:
            """
            Retrieve details for a specific agent instance, including its configuration.
            """
            return await AgentService.get_agent_instance(agent_class, agent_id, t)

        return self

    def update_agent_instance(self, route: str = "/classes/{agent_class}/instances/{agent_id}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_agent_instance(
            agent_class: str,
            agent_id: str,
            request: UpdateAgentInstanceDTO,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.agent.{agent_class}.{agent_id}"))
            ],
        ) -> FullAgentInstanceDTO:
            """
            Update the configuration for a specific agent instance.
            """
            await AgentService.update_agent_instance(agent_class, agent_id, request.configuration)

            # Return the updated instance
            from aihub_lib.i18n.LocaleHandler import LocaleHandler as LH
            from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
            from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument

            class_entity = AgentClassEntity.get_by_agent_class(agent_class)
            config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)

            if not class_entity or not config_entity:
                raise HTTPException(status_code=404, detail=f"Agent instance {agent_class}/{agent_id} not found.")

            t = LH(locale="en")
            return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

        return self

    def delete_agent_instance(self, route: str = "/classes/{agent_class}/instances/{agent_id}") -> Self:
        from fastapi import Response, status

        @self.router.delete(route, tags=self.tags, status_code=status.HTTP_204_NO_CONTENT)
        async def delete_agent_instance(
            agent_class: str,
            agent_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.agent.{agent_class}.{agent_id}"))
            ],
        ) -> Response:
            """
            Delete an agent instance.
            """
            await AgentService.delete_agent_instance(agent_class, agent_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return self

    def get_agent_instance_threads(self, route: str = "/classes/{agent_class}/instances/{agent_id}/threads") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_instance_threads(
            agent_class: str,
            agent_id: str,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedThreadsResponse:
            """
            Retrieve all threads that a specific agent instance is part of.
            """
            access_level = AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id)
            total, threads = await AgentService.get_agent_instance_threads(
                agent_class=agent_class,
                agent_id=agent_id,
                t=t,
                page=page,
                page_size=page_size,
                user_id=None if access_level == AccessLevel.ACCESS_ADMIN else user.id,
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedThreadsResponse(
                threads=threads, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def get_all_agent_instances(self, route: str = "/instances") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_all_agent_instances(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            online: Annotated[bool | None, Query(description="Filter by online status")] = None,
        ) -> list[FullAgentInstanceDTO]:
            """
            Retrieve a list of all agent instances across all classes.
            Use `?online=true` for online instances only, `?online=false` for offline only.
            """
            agents = await AgentService.get_all_agent_instances(t, online=online)
            return [
                agent
                for agent in agents
                if AccessChecker.from_user(user).has_access_to_agent(agent.agent_class, agent.agent_id)
            ]

        return self
