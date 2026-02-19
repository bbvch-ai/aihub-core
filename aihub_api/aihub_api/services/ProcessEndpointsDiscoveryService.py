import logging
from asyncio import sleep
from typing import Annotated, override

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.dependencies.use_external_process_event_distributor import (
    use_external_process_event_distributor,
)
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events.discovery import ProcessClassDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.persistence.process.ProcessClassEntity import ProcessClassEntity
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from bson import ObjectId
from fastapi import Body, Depends, FastAPI, HTTPException, Path, Security
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from stringcase import snakecase

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.process.ProcessService import ProcessService
from aihub_api.services.EndpointsDiscoveryService import EndpointsDiscoveryService

logger = logging.getLogger(__name__)


class ProcessEndpointsDiscoveryService(EndpointsDiscoveryService):
    """
    This service ensures that new processes in the system are automatically registered.
    This ensures that the API and the Processes are decoupled.

    It broadcasts NATS discovery requests to find online process classes and:
    1. Updates their last_discovered timestamp (which determines online status)
    2. Registers/deregisters dynamic API endpoints at the CLASS level (not instance level)

    Endpoints use {process_id} as a FastAPI path parameter, with instance validation at request time.
    """

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        controller: ProcessController,
        locale_handler: LocaleHandler,
        discovery_interval: int = 60,
    ):
        super().__init__(nc, api_app, controller, locale_handler, discovery_interval)
        self.controller: ProcessController = controller
        self.topic_manager: ProcessTopicManager = ProcessTopicManager()

    @override
    async def _discover_and_register(self):
        """
        Discovers process classes via NATS broadcast and registers class-level endpoints.

        This method:
        1. Broadcasts a NATS discovery request to all running processes
        2. Collects responses and updates last_discovered timestamps in database
        3. Registers/deregisters dynamic API endpoints at the CLASS level (not instance level)

        Endpoints use {process_id} as a FastAPI path parameter, with instance validation at request time.
        """
        # Step 1: Discover which process classes are online via NATS broadcast
        discovered_classes: list[ProcessClassDTO] = await self._broadcast_discovery()

        online_class_names = {dto.process_class for dto in discovered_classes}

        # Step 2: Deregister endpoints for classes no longer online
        for process_class in list(self.registered_classes):
            if process_class not in online_class_names:
                self._deregister_endpoints_for_class(process_class)

        self.app.openapi_schema = None

        # Step 3: Register endpoints for newly discovered classes
        for process_class_dto in discovered_classes:
            if process_class_dto.process_class not in self.registered_classes:
                self._register_class_endpoints(process_class_dto)
                self.registered_classes.add(process_class_dto.process_class)
                logger.info(f"Registered class-level endpoints for process class: {process_class_dto.process_class}")

    async def _broadcast_discovery(self) -> list[ProcessClassDTO]:
        """
        Broadcasts a NATS discovery request to all processes and collects responses.
        Updates the last_discovered timestamp for responding process classes.

        Returns a list of ProcessClassDTO for all online process classes.
        """
        call_id = str(ObjectId())
        discovery_responses: list[ProcessClassDiscoveryResponseEvent] = []

        async def discovery_handler(event: ProcessClassDiscoveryResponseEvent, topic):
            discovery_responses.append(event)

        nc_publisher = NCPublisher("ProcessEndpointsDiscoveryServiceClassDiscoveryRequest", self.nc)
        nc_subscriber = ProcessNCSubscriber.for_process_class_discovery_response_events(
            self.nc,
            self.topic_manager,
            discovery_handler,
            call_id=call_id,
            subscriber_name="ProcessEndpointsDiscoveryServiceClassDiscoveryResponse",
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=self.topic_manager.get_process_class_discovery_subject_request(call_id=call_id),
        )

        # Wait briefly for responses
        await sleep(10)
        await nc_subscriber.stop()

        unique_classes_dict: dict[str, ProcessClassDTO] = {}

        for response in discovery_responses:
            unique_key = response.process_class

            if unique_key not in unique_classes_dict:
                process_class_dto = ProcessClassDTO.from_discovery_event(response)
                unique_classes_dict[unique_key] = process_class_dto

                # Persist the process class entity in database (updates last_discovered timestamp)
                ProcessClassEntity.create_or_update(
                    process_class=process_class_dto.process_class,
                    name=process_class_dto.name,
                    description=process_class_dto.description,
                    icon=process_class_dto.icon,
                    form=process_class_dto.form,
                    process_config_specs=process_class_dto.process_config_specs,
                    human_inputs=process_class_dto.human_inputs,
                    program_inputs=process_class_dto.program_inputs,
                    agent_inputs=process_class_dto.agent_inputs,
                    default_process_config=process_class_dto.default_process_config,
                )

        return list(unique_classes_dict.values())

    def _register_class_endpoints(self, process_class_dto: ProcessClassDTO):
        """Registers class-level endpoints with dynamic {process_id} path parameter."""
        process_class = process_class_dto.process_class

        for human_input in process_class_dto.human_inputs:
            self._register_human_endpoint(process_class, human_input, process_class_dto.default_process_config)

        for program_input in process_class_dto.program_inputs:
            self._register_program_endpoint(process_class, program_input, process_class_dto.default_process_config)

    def _get_endpoint_base_path_for_process_class(self, process_class: str) -> str:
        """Returns the base path for class-level endpoints with dynamic {process_id} path parameter."""
        return f"{self.controller.base_route}/classes/{process_class}/instances/{{process_id}}"

    def _deregister_endpoints_for_class(self, process_class: str):
        """Deregister all endpoints for a process class (class-level endpoints with dynamic {process_id})."""
        base_path = self._get_endpoint_base_path_for_process_class(process_class)

        for route in list(self.app.routes):
            if route.path.startswith(f"{base_path}/"):
                self.app.routes.remove(route)
                logger.info(f"Deregistered endpoint: {route.path}")

        self.registered_classes.discard(process_class)

    def _register_human_endpoint(
        self,
        process_class: str,
        human_input: HumanInSpecs,
        default_process_config: ProcessConfig,
    ):
        """Register endpoints that allow humans to interact with a process by getting and submitting forms."""
        base_path = self._get_endpoint_base_path_for_process_class(process_class)

        process_class_snake = snakecase(process_class)
        get_endpoint_name = f"get_form_for_{process_class_snake}_{human_input.route.replace('/', '_')}"
        post_endpoint_name = f"submit_form_for_{process_class_snake}_{human_input.route.replace('/', '_')}"

        if human_input.is_process_start:
            path = f"{base_path}{human_input.route}"
        else:
            path = f"{base_path}/{{process_walkthrough_id}}{human_input.route}"

        post_input_type = EventModelCreationService.create_input_model_from_specs(human_input.event_specs)

        if human_input.is_process_start:
            get_endpoint_creator = self._create_form_get_endpoint_process_start
            post_endpoint_creator = self._create_form_post_endpoint_process_start
        else:
            get_endpoint_creator = self._create_form_get_endpoint
            post_endpoint_creator = self._create_form_post_endpoint

        # GET endpoint that returns form
        logger.debug(f"Creating Human.In GET endpoint for form: {path} with name {get_endpoint_name}")
        self.app.add_api_route(
            path=path,
            endpoint=get_endpoint_creator(
                process_class=process_class,
                process_controller=self.controller,
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
                process_controller=self.controller,
                input_specs=human_input,
                default_process_config=default_process_config,
            ),
            methods=[human_input.method],
            name=post_endpoint_name,
            tags=["Processes"],
        )
        logger.info(f"Successfully registered endpoints for {process_class}")

    def _register_program_endpoint(
        self,
        process_class: str,
        program_input: ProgramInSpecs,
        default_process_config: ProcessConfig,
    ):
        """Register endpoints that allow programs to interact with a process submitting data."""
        base_path = self._get_endpoint_base_path_for_process_class(process_class)

        process_class_snake = snakecase(process_class)

        post_endpoint_name = f"submit_form_for_{process_class_snake}_{program_input.route.replace('/', '_')}"
        path = f"{base_path}{program_input.route}"

        post_input_type = EventModelCreationService.create_input_model_from_specs(program_input.event_specs)

        if program_input.is_process_start:
            endpoint_creator = self._create_form_post_endpoint_process_start
        else:
            endpoint_creator = self._create_form_post_endpoint

        logger.debug(f"Creating Program.In POST endpoint for form: {path} with name {post_endpoint_name}")
        self.app.add_api_route(
            path=path,
            endpoint=endpoint_creator(
                input_type=post_input_type,
                process_class=process_class,
                process_controller=self.controller,
                input_specs=program_input,
                default_process_config=default_process_config,
            ),
            methods=[program_input.method],
            name=post_endpoint_name,
            tags=["Processes"],
        )
        logger.info(f"Successfully registered endpoints for {process_class}")

    @staticmethod
    def _create_form_get_endpoint_process_start(
        process_class: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        """Creates an endpoint to retrieve a form for starting a process."""

        async def get_form(
            process_id: Annotated[str, Path(title="Process ID", description="The specific process instance ID")],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{{process_id}}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> HumanInDTO:
            config = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
            if not config:
                raise HTTPException(
                    status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found"
                )

            process_human_input_dtos = await ProcessService.get_process_start_forms(
                process_class=process_class,
                process_id=process_id,
                t=t,
            )
            process_dto = next(
                (
                    dto
                    for dto in process_human_input_dtos
                    if dto.route == input_specs.route and dto.method == input_specs.method
                ),
                None,
            )

            if not process_dto:
                raise HTTPException(status_code=404, detail="Work request not found in this walkthrough")

            return process_dto

        return get_form

    @staticmethod
    def _create_form_get_endpoint(
        process_class: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        """Create an endpoint to retrieve a form for continuing a process."""

        async def get_form(
            process_id: Annotated[str, Path(title="Process ID", description="The specific process instance ID")],
            process_walkthrough_id: Annotated[str, Path(title="Walkthrough ID", pattern=r"^[a-f0-9]{24}$")],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{{process_id}}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> HumanInDTO:
            config = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
            if not config:
                raise HTTPException(
                    status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found"
                )

            process_human_input_dtos = await ProcessService.get_process_open_forms(
                process_class=process_class,
                process_id=process_id,
                process_walkthrough_id=process_walkthrough_id,
                t=t,
            )
            process_dto = next(
                (
                    dto
                    for dto in process_human_input_dtos
                    if dto.route == input_specs.route and dto.method == input_specs.method
                ),
                None,
            )

            if not process_dto:
                raise HTTPException(status_code=404, detail="Work request not found in this walkthrough")

            return process_dto

        return get_form

    @staticmethod
    def _create_form_post_endpoint_process_start(
        input_type: type[BaseModel],
        process_class: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
        default_process_config: ProcessConfig,
    ):
        """Create an endpoint to submit a form for starting a process."""

        async def send_event(
            process_id: Annotated[str, Path(title="Process ID", description="The specific process instance ID")],
            work_event_input: Annotated[input_type, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{{process_id}}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
            if not config_entity:
                raise HTTPException(
                    status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found"
                )

            process_config = ProcessConfig(
                process_class=config_entity.process_class,
                process_id=config_entity.process_id,
                name=config_entity.name if config_entity.name else default_process_config.name,
                description=(
                    config_entity.description if config_entity.description else default_process_config.description
                ),
            )

            return await ProcessService.submit_process_start_form(
                process_class=process_class,
                process_id=process_id,
                route=input_specs.route,
                method=input_specs.method,
                raw_event_data=work_event_input.model_dump(),
                external_process_event_distributor=external_process_event_distributor,
                user=user,
                t=t,
                process_config=process_config,
            )

        return send_event

    @staticmethod
    def _create_form_post_endpoint(
        input_type: type[BaseModel],
        process_class: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
        default_process_config: ProcessConfig,  # Used for fallback values
    ):
        """Create an endpoint to submit a form for continuing a process."""

        async def send_event(
            process_id: Annotated[str, Path(title="Process ID", description="The specific process instance ID")],
            process_walkthrough_id: Annotated[str, Path(title="Walkthrough ID", pattern=r"^[a-f0-9]{24}$")],
            work_event_input: Annotated[input_type, Body],
            external_process_event_distributor: Annotated[
                ExternalProcessEventDistributor, Depends(use_external_process_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{{process_id}}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> SubmittedFormDTO:
            config = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
            if not config:
                raise HTTPException(
                    status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found"
                )

            return await ProcessService.submit_process_open_form(
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
