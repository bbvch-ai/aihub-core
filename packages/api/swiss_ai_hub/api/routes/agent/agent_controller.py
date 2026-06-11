import asyncio
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Query, Security
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.access.access_level import AccessLevel
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.agents import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.pagination.type.page_number import PageNumber
from swiss_ai_hub.api.pagination.type.page_size import PageSize
from swiss_ai_hub.api.routes.agent.agent_file_upload_service import AgentFileUploadService
from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.agent.dependencies.use_agent_file_upload import use_agent_file_upload_service
from swiss_ai_hub.api.routes.agent.dto.agent_class_dto import AgentClassDTO
from swiss_ai_hub.api.routes.agent.dto.agent_file_upload_request import AgentFileUploadRequest
from swiss_ai_hub.api.routes.agent.dto.agent_file_upload_response import AgentFileUploadResponse
from swiss_ai_hub.api.routes.agent.dto.agent_file_validation_request import AgentFileValidationRequest
from swiss_ai_hub.api.routes.agent.dto.agent_file_validation_response import AgentFileValidationResponse
from swiss_ai_hub.api.routes.agent.dto.create_agent_instance_request import CreateAgentInstanceRequest
from swiss_ai_hub.api.routes.agent.dto.full_agent_instance_dto import FullAgentInstanceDTO
from swiss_ai_hub.api.routes.agent.dto.update_agent_instance_dto import UpdateAgentInstanceDTO
from swiss_ai_hub.api.routes.thread.dto.paginated_threads_response import PaginatedThreadsResponse


class AgentController(TenantScopedController):
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

    _AGENT_INSTANCE_ROUTE = "/classes/{agent_class}/instances/{agent_id}"

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
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.{agent_class}"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullAgentInstanceDTO:
            """
            Create a new agent instance from an existing agent class.
            """
            return await AgentService.create_agent_instance(agent_class, request, t, user=user)

        return self

    def get_agent_instance(self, route: str = _AGENT_INSTANCE_ROUTE) -> Self:
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

    def update_agent_instance(self, route: str = _AGENT_INSTANCE_ROUTE) -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_agent_instance(
            agent_class: str,
            agent_id: str,
            request: UpdateAgentInstanceDTO,
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.agent.{agent_class}.{agent_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullAgentInstanceDTO:
            """
            Update the configuration for a specific agent instance.
            """
            await AgentService.update_agent_instance(agent_class, agent_id, request.configuration, t, user=user)

            class_entity = AgentClassEntity.get_by_agent_class(agent_class)
            config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)

            if not class_entity or not config_entity:
                raise HTTPException(status_code=404, detail=f"Agent instance {agent_class}/{agent_id} not found.")

            return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

        return self

    def delete_agent_instance(self, route: str = _AGENT_INSTANCE_ROUTE) -> Self:
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
            agent_class: Annotated[str | None, Query(description="Filter by agent class")] = None,
            search: Annotated[str | None, Query(description="Search by agent name")] = None,
        ) -> list[FullAgentInstanceDTO]:
            """
            Retrieve a list of all agent instances across all classes.
            Use `?online=true` for online instances only, `?online=false` for offline only.
            Use `?search={agentName}` to search an agent with its name.
            """
            agents = await AgentService.get_all_agent_instances(
                t, online=online, search=search, agent_class=agent_class
            )
            return [
                agent
                for agent in agents
                if AccessChecker.from_user(user).has_access_to_agent(agent.agent_class, agent.agent_id)
            ]

        return self

    def initiate_file_upload(
        self, route: str = "/classes/{agent_class}/instances/{agent_id}/files/upload/initiate"
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def initiate_file_upload(
            agent_class: str,
            agent_id: str,
            request: AgentFileUploadRequest,
            _: Annotated[
                UserIdentity,
                Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}")),
            ],
            upload_service: Annotated[AgentFileUploadService, Depends(use_agent_file_upload_service)],
        ) -> AgentFileUploadResponse:
            """Initiate a file upload by generating a presigned PUT URL for the agent's dedicated bucket."""
            presigned_url, file_id = await asyncio.to_thread(
                upload_service.generate_upload_url,
                agent_class=agent_class,
                agent_id=agent_id,
                content_type=request.content_type,
                filename=request.filename,
            )
            return AgentFileUploadResponse(
                upload_url=presigned_url,
                file_id=file_id,
                expires_in=AgentFileUploadService.UPLOAD_URL_LIFETIME_SECONDS,
            )

        return self

    def validate_file_upload(
        self, route: str = "/classes/{agent_class}/instances/{agent_id}/files/upload/validate"
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def validate_file_upload(
            agent_class: str,
            agent_id: str,
            request: AgentFileValidationRequest,
            _: Annotated[
                UserIdentity,
                Security(self.user_with_permission("aihub.user.agent.{agent_class}.{agent_id}")),
            ],
            upload_service: Annotated[AgentFileUploadService, Depends(use_agent_file_upload_service)],
        ) -> AgentFileValidationResponse:
            """Validate that a file was successfully uploaded to the agent's dedicated bucket."""
            exists = await asyncio.to_thread(
                upload_service.verify_file_exists,
                agent_class=agent_class,
                agent_id=agent_id,
                file_id=request.file_id,
                filename=request.filename,
            )
            return AgentFileValidationResponse(
                file_id=request.file_id,
                exists=exists,
            )

        return self
