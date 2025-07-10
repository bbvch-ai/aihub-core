from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.ProcessService import ProcessService


class ProcessController(Controller):
    name = LocaleString(en="Processes")
    description = LocaleString(en="Interacts with processes")
    icon = "carbon:ibm-event-processing"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/processes", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_processes(self, route: str = "/") -> "ProcessController":
        @self.router.get(route, tags=self.tags)
        async def get_processes(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.process.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[ProcessDTO]:
            """
            Retrieve a list of all processes, both online (discoverable) and offline (not discoverable).
            """
            processes = await ProcessService.get_processes(nc, t)
            return [
                process
                for process in processes
                if AccessChecker.from_user(user).has_access_to_process(process.process_class, process.process_id)
            ]

        return self

    def discover_processes(self, route: str = "/discover") -> "ProcessController":
        @self.router.get(route, tags=self.tags)
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
        @self.router.get(route, tags=self.tags)
        async def get_process(
            nc: Annotated[NATS, Depends(use_nats)],
            process_class: str,
            process_id: str,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.process.{process_class}.{process_id}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessDTO:
            """
            Retrieve details for a specific process. Raises 403 if the user lacks access.
            """
            return await ProcessService.get_process(nc, process_class, process_id, t)

        return self
