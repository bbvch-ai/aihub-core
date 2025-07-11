import asyncio
import logging
import time
from typing import Annotated, Any

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.process.dto.ProcessHumanInputDto import ProcessHumanInputDto
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_process_event_distributor import (
    use_external_process_event_distributor,
)
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events.discovery.process.ProcessDiscoveryResponseEvent import HumanInSpecs, ProgramInSpecs
from fastapi import Body, Depends, FastAPI, Path, Security, HTTPException
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from stringcase import snakecase

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.process.ProcessService import ProcessService

logger = logging.getLogger(__name__)


class ProcessEndpointsDiscoveryService:
    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        process_controller: ProcessController,
        locale_handler: LocaleHandler,
        discovery_interval: int = 60,
    ):
        self.nc: NATS = nc
        self.app: FastAPI = api_app
        self.process_controller: ProcessController = process_controller
        self.locale_handler: LocaleHandler = locale_handler
        self.discovery_interval: int = discovery_interval
        self.registered_processes: set[tuple[str, str]] = set()
        self.running: bool = False
        self.task: asyncio.Task | None = None

    async def start(self):
        if self.running:
            logger.warning("Process discovery service is already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._discovery_loop())
        logger.info("Process discovery service started")

    async def stop(self):
        if not self.running:
            logger.warning("Process discovery service is not running")
            return

        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("Process discovery service stopped")

    async def _discovery_loop(self):
        while self.running:
            try:
                logger.debug("Starting process discovery")
                await self._discover_and_register_processes()
            except Exception as e:
                logger.exception(f"Error in process discovery: {e}")

            await asyncio.sleep(self.discovery_interval)

    async def _discover_and_register_processes(self):
        processes: list[ProcessDTO] = await ProcessService.discover_processes(self.nc, self.locale_handler)

        for registered_process_class, registered_process_id in list(self.registered_processes):
            self._deregister_process_endpoints(registered_process_class, registered_process_id)

        self.app.openapi_schema = None

        for process in processes:
            process_key = (process.process_class, process.process_id)

            for human_input in process.human_inputs:
                self._register_human_endpoint(process.process_class, process.process_id, human_input)

            for process_input in process.program_inputs:
                self._register_program_endpoint(process.process_class, process.process_id, process_input)

            self.registered_processes.add(process_key)
            logger.info(f"Registered endpoints for process: {process.process_class}.{process.process_id}")

    def _get_process_endpoint_name(self, process_class: str, process_id: str) -> str:
        return f"{self.process_controller.base_route}/{process_class}/{process_id}"

    def _deregister_process_endpoints(self, process_class: str, process_id: str):
        base_path = self._get_process_endpoint_name(process_class, process_id)

        for route in list(self.app.routes):
            if route.path.startswith(f"{base_path}/"):
                self.app.routes.remove(route)
                logger.info(f"Deregistered endpoint: {route.path}")

        # Remove from registered processes
        self.registered_processes.discard((process_class, process_id))

    def _register_human_endpoint(
        self,
        process_class: str,
        process_id: str,
        human_input: HumanInSpecs,
    ):
        base_path = self._get_process_endpoint_name(process_class, process_id)

        process_class_snake = snakecase(process_class)
        process_id_snake = snakecase(process_id)
        get_endpoint_name = (
            f"get_form_for_{process_class_snake}_{process_id_snake}_{human_input.route.replace('/', '_')}"
        )
        post_endpoint_name = (
            f"submit_form_for_{process_class_snake}_{process_id_snake}_{human_input.route.replace('/', '_')}"
        )

        if human_input.is_process_start:
            path = f"{base_path}{human_input.route}"
        else:
            path = f"{base_path}/{{process_walkthrough_id}}{human_input.route}"

        post_input_type = EventModelCreationService.create_input_model_from_specs(human_input.event_specs)

        if human_input.is_process_start:
            get_endpoint_creator = self.create_form_get_endpoint_process_start
            post_endpoint_creator = self.create_form_post_endpoint_process_start
        else:
            get_endpoint_creator = self.create_form_get_endpoint
            post_endpoint_creator = self.create_form_post_endpoint

        # GET endpoint that returns form
        logger.debug(f"Creating Human.In GET endpoint for form: {path} with name {get_endpoint_name}")
        self.app.add_api_route(
            path=path,
            endpoint=get_endpoint_creator(
                process_class=process_class,
                process_id=process_id,
                process_controller=self.process_controller,
                input_specs=human_input,
            ),
            methods=["GET"],
            name=get_endpoint_name,
            tags=["Processes"],
        )

        # POST endpoint that accepts form
        logger.debug(f"Creating Human.In POST endpoint for form: {path} with name {post_endpoint_name}")
        self.app.add_api_route(
            path=path,
            endpoint=post_endpoint_creator(
                input_type=post_input_type,
                process_class=process_class,
                process_id=process_id,
                process_controller=self.process_controller,
                input_specs=human_input,
            ),
            methods=[human_input.method],
            name=post_endpoint_name,
            tags=["Processes"],
        )
        logger.info(f"Successfully registered endpoints for {process_class}/{process_id}")

    def _register_program_endpoint(
        self,
        process_class: str,
        process_id: str,
        program_input: ProgramInSpecs,
    ):
        base_path = self._get_process_endpoint_name(process_class, process_id)

        process_class_snake = snakecase(process_class)
        process_id_snake = snakecase(process_id)


        post_endpoint_name = (
            f"submit_form_for_{process_class_snake}_{process_id_snake}_{program_input.route.replace('/', '_')}"
        )
        path = f"{base_path}{program_input.route}"

        post_input_type = EventModelCreationService.create_input_model_from_specs(program_input.event_specs)

        if program_input.is_process_start:
            endpoint_creator = self.create_form_post_endpoint_process_start
        else:
            endpoint_creator = self.create_form_post_endpoint

        logger.debug(f"Creating Program.In POST endpoint for form: {path} with name {post_endpoint_name}")
        self.app.add_api_route(
            path=path,
            endpoint=endpoint_creator(
                input_type=post_input_type,
                process_class=process_class,
                process_id=process_id,
                process_controller=self.process_controller,
                input_specs=program_input,
            ),
            methods=[program_input.method],
            name=post_endpoint_name,
            tags=["Processes"],
        )
        logger.info(f"Successfully registered endpoints for {process_class}/{process_id}")

    @staticmethod
    def create_form_get_endpoint_process_start(
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        async def get_form(
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessHumanInputDto:
            process_human_input_dtos = await ProcessService.get_process_start_forms(
                nc=nc,
                process_class=process_class,
                process_id=process_id,
                t=t,
            )
            process_dto = next((dto for dto in process_human_input_dtos if dto.route == input_specs.route and dto.method == input_specs.method), None)

            if not process_dto:
                raise HTTPException(status_code=404, detail="Work request not found in this walkthrough")

            return process_dto

        return get_form

    @staticmethod
    def create_form_get_endpoint(
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        async def get_form(
            process_walkthrough_id: Annotated[str, Path(title="Walkthrough ID", pattern="^[a-f0-9]{24}$")],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessHumanInputDto:
            process_human_input_dtos = await ProcessService.get_process_open_forms(
                nc=nc,
                process_class=process_class,
                process_id=process_id,
                process_walkthrough_id=process_walkthrough_id,
                t=t,
            )
            process_dto = next((dto for dto in process_human_input_dtos if dto.route == input_specs.route and dto.method == input_specs.method), None)

            if not process_dto:
                raise HTTPException(status_code=404, detail="Work request not found in this walkthrough")

            return process_dto

        return get_form

    @staticmethod
    def create_form_post_endpoint_process_start(
        input_type: type[BaseModel],
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
    ):
        async def send_event(
            work_event_input: Annotated[input_type, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            return await ProcessService.submit_process_start_form(
                nc=nc,
                process_class=process_class,
                process_id=process_id,
                route=input_specs.route,
                method=input_specs.method,
                raw_event_data=work_event_input.model_dump(),
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
            )

        return send_event

    @staticmethod
    def create_form_post_endpoint(
        input_type: type[BaseModel],
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
    ):
        async def send_event(
            process_walkthrough_id: Annotated[str, Path(title="Walkthrough ID", pattern="^[a-f0-9]{24}$")],
            work_event_input: Annotated[input_type, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            return await ProcessService.submit_process_open_form(
                nc=nc,
                process_class=process_class,
                process_id=process_id,
                process_walkthrough_id=process_walkthrough_id,
                route=input_specs.route,
                method=input_specs.method,
                raw_event_data=work_event_input.model_dump(),
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
            )

        return send_event
