from typing import Annotated, Self

from fastapi import Body, Depends, HTTPException, Security
from fastapi.params import Query
from swiss_ai_hub.core.auth.access.AccessChecker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity
from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.nats.distributor.dependencies.use_external_process_event_distributor import (
    use_external_process_event_distributor,
)
from swiss_ai_hub.core.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from swiss_ai_hub.core.persistence.process.ProcessClassEntity import ProcessClassEntity
from swiss_ai_hub.core.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from swiss_ai_hub.core.processes.ProcessConfig import ProcessConfig
from swiss_ai_hub.core.routes.Controller import Controller

from swiss_ai_hub.api.i18n.ApiLocaleString import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.pagination.type.PageNumber import PageNumber
from swiss_ai_hub.api.pagination.type.PageSize import PageSize
from swiss_ai_hub.api.routes.process.dto import PaginatedProcessWalkthroughsResponse
from swiss_ai_hub.api.routes.process.dto.CreateProcessInstanceRequest import CreateProcessInstanceRequest
from swiss_ai_hub.api.routes.process.dto.FullProcessInstanceDTO import FullProcessInstanceDTO
from swiss_ai_hub.api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from swiss_ai_hub.api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from swiss_ai_hub.api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from swiss_ai_hub.api.routes.process.dto.UpdateProcessInstanceDTO import UpdateProcessInstanceDTO
from swiss_ai_hub.api.routes.process.ProcessService import ProcessService


class ProcessController(Controller):
    """
    A controller managing endpoints related to processes, including classes and instances.

    ### API Structure
    - Process Classes: `/processes/classes` - Process definitions/templates
    - Process Instances: `/processes/classes/{process_class}/instances` - Configured deployments
    - Cross-class instances: `/processes/instances` - All instances across classes
    - Form interaction: Endpoints for human/program form submission
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.process.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.process.description")
    icon = "mage:arrowlist"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/processes", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    # ==================== Process Classes Endpoints ====================

    def get_process_classes(self, route: str = "/classes") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_process_classes(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.process.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            online: Annotated[bool | None, Query(description="Filter by online status")] = None,
        ) -> list[ProcessClassDTO]:
            """
            Retrieve all available process classes.
            Use `?online=true` for online classes only, `?online=false` for offline only.
            """
            return await ProcessService.get_process_classes(t, online=online)

        return self

    def get_process_class(self, route: str = "/classes/{process_class}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_process_class(
            process_class: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.process.{process_class}.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessClassDTO:
            """Retrieve details for a specific process class."""
            return await ProcessService.get_process_class(process_class, t)

        return self

    def get_process_class_instances(self, route: str = "/classes/{process_class}/instances") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_process_class_instances(
            process_class: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[FullProcessInstanceDTO]:
            """Retrieve all instances of a specific process class."""
            instances = await ProcessService.get_process_class_instances(process_class, t)
            return [
                instance
                for instance in instances
                if AccessChecker.from_user(user).has_access_to_process(instance.process_class, instance.process_id)
            ]

        return self

    def create_process_instance(self, route: str = "/classes/{process_class}/instances") -> Self:
        from fastapi import status

        @self.router.post(route, tags=self.tags, status_code=status.HTTP_201_CREATED)
        async def create_process_instance(
            process_class: str,
            request: CreateProcessInstanceRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.process.{process_class}.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullProcessInstanceDTO:
            """Create a new process instance from an existing process class."""
            return await ProcessService.create_process_instance(process_class, request, t)

        return self

    def get_process_instance(self, route: str = "/classes/{process_class}/instances/{process_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_process_instance(
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullProcessInstanceDTO:
            """Retrieve details for a specific process instance, including its configuration."""
            return await ProcessService.get_process_instance(process_class, process_id, t)

        return self

    def update_process_instance(self, route: str = "/classes/{process_class}/instances/{process_id}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_process_instance(
            process_class: str,
            process_id: str,
            request: UpdateProcessInstanceDTO,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> FullProcessInstanceDTO:
            """Update the configuration for a specific process instance."""
            await ProcessService.update_process_instance(process_class, process_id, request.configuration)

            class_entity = ProcessClassEntity.get_by_process_class(process_class)
            config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)

            if not class_entity or not config_entity:
                raise HTTPException(status_code=404, detail=f"Process instance {process_class}/{process_id} not found.")

            return FullProcessInstanceDTO.from_class_and_config(class_entity, config_entity, t)

        return self

    def delete_process_instance(self, route: str = "/classes/{process_class}/instances/{process_id}") -> Self:
        from fastapi import Response, status

        @self.router.delete(route, tags=self.tags, status_code=status.HTTP_204_NO_CONTENT)
        async def delete_process_instance(
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.process.{process_class}.{process_id}"))
            ],
        ) -> Response:
            """Delete a process instance."""
            await ProcessService.delete_process_instance(process_class, process_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        return self

    def get_all_process_instances(self, route: str = "/instances") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_all_process_instances(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            online: Annotated[bool | None, Query(description="Filter by online status")] = None,
        ) -> list[FullProcessInstanceDTO]:
            """
            Retrieve a list of all process instances across all classes.
            Use `?online=true` for online instances only, `?online=false` for offline only.
            """
            instances = await ProcessService.get_all_process_instances(t, online=online)
            return [
                instance
                for instance in instances
                if AccessChecker.from_user(user).has_access_to_process(instance.process_class, instance.process_id)
            ]

        return self

    # ==================== Walkthrough Endpoints ====================

    def get_process_walkthroughs(
        self, route: str = "/classes/{process_class}/instances/{process_id}/walkthroughs"
    ) -> Self:
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process_walkthroughs(
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedProcessWalkthroughsResponse:
            """Get paginated process walkthroughs with detailed step information for a specific process."""
            total, walkthroughs = await ProcessService.get_process_walkthroughs(
                process_class, process_id, t, page, page_size
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedProcessWalkthroughsResponse(
                walkthroughs=walkthroughs,
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        return self

    # ==================== Form Interaction Endpoints ====================

    def get_process_start_forms(
        self, route: str = "/classes/{process_class}/instances/{process_id}/start_forms"
    ) -> Self:
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process_start_forms(
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[HumanInDTO]:
            """Returns a list of formkit forms that the user can submit to start the process."""
            return await ProcessService.get_process_start_forms(process_class, process_id, t)

        return self

    def get_process_open_forms(
        self, route: str = "/classes/{process_class}/instances/{process_id}/{process_walkthrough_id}/open_forms"
    ) -> Self:
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process_open_forms(
            process_class: str,
            process_id: str,
            process_walkthrough_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[HumanInDTO]:
            """Returns a list of formkit forms that the user can submit to continue the given process walkthrough"""
            return await ProcessService.get_process_open_forms(process_class, process_id, process_walkthrough_id, t)

        return self

    def send_process_start_form(
        self, route: str = "/classes/{process_class}/instances/{process_id}/submit_start_form"
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def send_process_start_form(
            process_class: str,
            process_id: str,
            submission_route: Annotated[str, Query(title="Route to which human input should be submitted")],
            submission_method: Annotated[str, Query(title="Method using which human input should be submitted")],
            data: Annotated[dict, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            """Submit an object satisfying a form to start a process."""
            config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
            if not config_entity:
                raise HTTPException(
                    status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found."
                )

            process_config = ProcessConfig(
                process_class=process_class,
                process_id=process_id,
                name=config_entity.name.to_locale_string() if config_entity.name else None,
                description=config_entity.description.to_locale_string() if config_entity.description else None,
                icon=config_entity.icon,
            )

            return await ProcessService.submit_process_start_form(
                process_class=process_class,
                process_id=process_id,
                route=submission_route,
                method=submission_method,
                raw_event_data=data,
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
                process_config=process_config,
            )

        return self

    def send_process_open_form(
        self,
        route: str = "/classes/{process_class}/instances/{process_id}/{process_walkthrough_id}/submit_open_form",
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def send_process_open_form(
            process_class: str,
            process_id: str,
            process_walkthrough_id: str,
            submission_route: Annotated[str, Query(title="Route to which human input should be submitted")],
            submission_method: Annotated[str, Query(title="Method using which human input should be submitted")],
            data: Annotated[dict, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            """Submit an object satisfying a form to continue a process walkthrough."""
            return await ProcessService.submit_process_open_form(
                process_class=process_class,
                process_id=process_id,
                process_walkthrough_id=process_walkthrough_id,
                route=submission_route,
                method=submission_method,
                raw_event_data=data,
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
            )

        return self
