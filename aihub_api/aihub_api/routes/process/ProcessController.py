from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_process_event_distributor import (
    use_external_process_event_distributor,
)
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Security
from fastapi.params import Query
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.process.dto import PaginatedProcessWalkthroughsResponse
from aihub_api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_api.routes.process.ProcessService import ProcessService


class ProcessController(Controller):
    """
    The process controller is a dynamic controller that exposed api endpoints to interact with agentic processes.

    An agentic process is a pre-defined process in which humans, agents and programs cooperate to achieve a desired
    outcome. While agents interact with the process behind the scenes using their dedicated event system,
    human and programs communicate with processes using dedicated API endpoints.

    This controller both exposes static endpoints to discover processes and interact with them through pre-defined
    endpoints. However, note that this controller also exposes dynamic endpoints generated on-the-fly based on the
    process definition. Hence, there are always two ways in which a human or program can post data to a process:
    - Through the static methods like send_process_start_form or send_process_open_form by providing query parameters
      for the route and method: POST:/{process_class}/{process_id}/submit_start_form?route=<route>&method=<method>.
    - By actually submitting the data to the dynamic endpoints generated on-the-fly, aka posting (or putting, depending
      on the HTTP method) to the dynamic route [<METHOD>]:/{process_class}/{process_id}/{<route>}.
    The same principle holds true for endpoints that return formkit form definitions.
    """

    name = LocaleString(en="Workflows", de="Arbeitsabläufe", fr="Flux de travail", it="Flussi di lavoro")
    description = LocaleString(
        en="Manage automated business processes",
        de="Automatisierte Geschäftsprozesse verwalten",
        fr="Gérez les processus métier automatisés",
        it="Gestisci processi aziendali automatizzati",
    )
    icon = "carbon:ibm-event-processing"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/processes", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_processes(self, route: str = "/") -> "ProcessController":
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_processes(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[ProcessDTO]:
            """
            Retrieve a list of all processes, both online (discoverable) and offline (not discoverable).
            Filters out processes the user cannot access.
            """
            processes = await ProcessService.get_processes(nc, t)
            return [
                process
                for process in processes
                if AccessChecker.from_user(user).has_access_to_process(process.process_class, process.process_id)
            ]

        return self

    def discover_processes(self, route: str = "/discover") -> "ProcessController":
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def discover_processes(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[ProcessDTO]:
            """
            Retrieve a list of all online (discoverable) processes. Filters out processes the user cannot access.
            """
            processes = await ProcessService.discover_processes(nc, t)
            return [
                process
                for process in processes
                if AccessChecker.from_user(user).has_access_to_process(process.process_class, process.process_id)
            ]

        return self

    def get_process(self, route: str = "/{process_class}/{process_id}") -> "ProcessController":
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process(
            nc: Annotated[NATS, Depends(use_nats)],
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessDTO:
            """Retrieve details for a specific process."""
            return await ProcessService.get_process(nc, process_class, process_id, t)

        return self

    def get_process_walkthroughs(
        self, route: str = "/{process_class}/{process_id}/walkthroughs"
    ) -> "ProcessController":
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

    def get_process_start_forms(self, route: str = "/{process_class}/{process_id}/start_forms") -> "ProcessController":
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process_start_forms(
            process_class: str,
            process_id: str,
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[HumanInDTO]:
            """Returns a list of formkit forms that the user can submit to start the process."""
            # TODO: Filter for forms that the user has access to
            return await ProcessService.get_process_start_forms(nc, process_class, process_id, t)

        return self

    def get_process_open_forms(
        self, route: str = "/{process_class}/{process_id}/{process_walkthrough_id}/open_forms"
    ) -> "ProcessController":
        @self.router.get(route, tags=self.tags, response_model_exclude_none=True)
        async def get_process_open_forms(
            process_class: str,
            process_id: str,
            process_walkthrough_id: str,
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[HumanInDTO]:
            """Returns a list of formkit forms that the user can submit to continue the given process walkthrough"""
            # TODO: Filter for forms that the user has access to
            return await ProcessService.get_process_open_forms(nc, process_class, process_id, process_walkthrough_id, t)

        return self

    def send_process_start_form(
        self, route: str = "/{process_class}/{process_id}/submit_start_form"
    ) -> "ProcessController":
        @self.router.post(route, tags=self.tags)
        async def send_process_start_form(
            process_class: str,
            process_id: str,
            submission_route: Annotated[str, Query(title="Route to which human input should be submitted")],
            submission_method: Annotated[str, Query(title="Method using which human input should be submitted")],
            data: Annotated[dict, Body],
            nc: Annotated[NATS, Depends(use_nats)],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            """Submit an object satisfying a form to start a process"""
            # TODO: Check that user has access to form
            process = await ProcessService.discover_process_instance(
                nc=nc, process_class=process_class, process_id=process_id
            )
            return await ProcessService.submit_process_start_form(
                nc=nc,
                process_class=process_class,
                process_id=process_id,
                route=submission_route,
                method=submission_method,
                raw_event_data=data,
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
                process_config=process.process_config,
            )

        return self

    def send_process_open_form(
        self, route: str = "/{process_class}/{process_id}/{process_walkthrough_id}/submit_open_form"
    ) -> "ProcessController":
        @self.router.post(route, tags=self.tags)
        async def send_process_open_form(
            process_class: str,
            process_id: str,
            process_walkthrough_id: str,
            submission_route: Annotated[str, Query(title="Route to which human input should be submitted")],
            submission_method: Annotated[str, Query(title="Method using which human input should be submitted")],
            data: Annotated[dict, Body],
            nc: Annotated[NATS, Depends(use_nats)],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            """Submit an object satisfying a form to continue a process walkthrough"""
            # TODO: Check that user has access to form
            return await ProcessService.submit_process_open_form(
                nc=nc,
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
