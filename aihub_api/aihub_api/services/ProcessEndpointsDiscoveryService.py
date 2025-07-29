import logging
from typing import Annotated

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_process_event_distributor import (
    use_external_process_event_distributor,
)
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events import InstanceDiscoveryRequestEvent
from aihub_lib.nats.events.discovery import ProcessInstanceDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics import ProcessInstanceDiscoveryTopic
from aihub_lib.persistence.process.ProcessEntity import ProcessConfig
from fastapi import Body, Depends, FastAPI, HTTPException, Path, Security
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from stringcase import snakecase
from typing_extensions import override

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.process.dto.ProcessHumanInDto import ProcessHumanInDto
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_api.routes.process.ProcessController import ProcessController
from aihub_api.routes.process.ProcessService import ProcessService
from aihub_api.services.EndpointsDiscoveryService import EndpointsDiscoveryService

logger = logging.getLogger(__name__)


class ProcessEndpointsDiscoveryService(EndpointsDiscoveryService):
    """
    This service ensures that new processes in the system are automatically registered.
    This ensures that the API and the Processes are decoupled.
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

        self.nc_publisher: NCPublisher[ProcessInstanceDiscoveryResponseEvent] | None = None
        self.discovery_event_subscriber: NCSubscriber[InstanceDiscoveryRequestEvent] | None = None

    async def _discovery_handler(self, event: InstanceDiscoveryRequestEvent, topic: ProcessInstanceDiscoveryTopic):
        """
        Responds to discovery requests by publishing a ProcessDiscoveryResponseEvent that includes the basic
        process configuration as well as some carefully crafted event specifications.
        """
        logger.debug(f"Received discovery request for {topic.process_class} with id {topic.process_id}.")

        subject = self.topic_manager.get_process_instance_discovery_subject_response(
            topic.call_id, topic.process_class, topic.process_id
        )

        process_instances: list[ProcessInstanceDTO] = []
        if topic.process_class == "*":
            process_instances = await ProcessService.discover_process_instances(self.nc)

            if topic.process_id != "*":
                process_instances = [process for process in process_instances if process.process_id == topic.process_id]

        elif topic.process_id == "*":
            process_instances = await ProcessService.discover_process_instances_by_class(self.nc, topic.process_class)

        else:
            process_instances.append(
                await ProcessService.discover_process_instance(self.nc, topic.process_class, topic.process_id)
            )

        for process_instance in process_instances:
            process_discovery_response_event = process_instance.to_discovery_response_event()
            await self.nc_publisher.publish_event(process_discovery_response_event, subject)

    @override
    async def start(self):
        started = await super().start()
        if not started:
            logger.debug("Process discovery service already running")
            return

        self.discovery_event_subscriber = ProcessNCSubscriber.for_process_instance_discovery_request_events(
            nc=self.nc,
            topic_manager=ProcessTopicManager(),
            handler=self._discovery_handler,
        )
        await self.discovery_event_subscriber.start()
        logger.info("Process discovery service started")

    @override
    async def stop(self):
        stopped = await super().stop()
        if not stopped:
            logger.debug("Process discovery service already stopped")
            return

        await self.discovery_event_subscriber.stop()
        logger.info("Process discovery service stopped")

    @override
    async def _discover_and_register(self):
        """
        Discovers processes and registers endpoints for retrieving and submitting forms to start / continue the process.
        """
        processes: list[ProcessInstanceDTO] = await ProcessService.discover_process_instances(self.nc)

        # Deregister old endpoints
        for registered_process_class, registered_process_id in list(self.registered_entities):
            self._deregister_endpoints(registered_process_class, registered_process_id)
        self.app.openapi_schema = None

        # Register new endpoints for configured processes
        for process in processes:
            process_key = (process.process_class, process.process_id)

            for human_input in process.human_inputs:
                self._register_human_endpoint(
                    process.process_class, process.process_id, human_input, process.process_config
                )

            for process_input in process.program_inputs:
                self._register_program_endpoint(
                    process.process_class, process.process_id, process_input, process.process_config
                )

            self.registered_entities.add(process_key)
            logger.info(f"Registered endpoints for configured process: {process.process_class}.{process.process_id}")

    def _register_human_endpoint(
        self,
        process_class: str,
        process_id: str,
        human_input: HumanInSpecs,
        process_config: ProcessConfig,
    ):
        """Register endpoints that allow humans to interact with a process by getting and submitting forms."""
        base_path = self._get_endpoint_base_path(process_class, process_id)

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
                process_id=process_id,
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
                process_id=process_id,
                process_controller=self.controller,
                input_specs=human_input,
                process_config=process_config,
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
        process_config: ProcessConfig,
    ):
        """Register endpoints that allow programs to interact with a process submitting data."""
        base_path = self._get_endpoint_base_path(process_class, process_id)

        process_class_snake = snakecase(process_class)
        process_id_snake = snakecase(process_id)

        post_endpoint_name = (
            f"submit_form_for_{process_class_snake}_{process_id_snake}_{program_input.route.replace('/', '_')}"
        )
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
                process_id=process_id,
                process_controller=self.controller,
                input_specs=program_input,
                process_config=process_config,
            ),
            methods=[program_input.method],
            name=post_endpoint_name,
            tags=["Processes"],
        )
        logger.info(f"Successfully registered endpoints for {process_class}/{process_id}")

    @staticmethod
    def _create_form_get_endpoint_process_start(
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        """Creates an endpoint to retrieve a form for starting a process."""

        async def get_form(
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessHumanInDto:
            # TODO: Ensure the user has the right to fetch this form
            process_human_input_dtos = await ProcessService.get_process_start_forms(
                nc=nc,
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
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs,
    ):
        """Create an endpoint to retrieve a form for continuing a process."""

        async def get_form(
            process_walkthrough_id: Annotated[str, Path(title="Walkthrough ID", pattern="^[a-f0-9]{24}$")],
            _: Annotated[
                UserIdentity,
                Security(process_controller.user_with_permission(f"aihub.user.process.{process_class}.{process_id}")),
            ],
            nc: Annotated[NATS, Depends(use_nats)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ProcessHumanInDto:
            # TODO: Ensure the user has the right to fetch this form
            process_human_input_dtos = await ProcessService.get_process_open_forms(
                nc=nc,
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
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
        process_config: ProcessConfig,
    ):
        """Create an endpoint to submit a form for starting a process."""

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
            # TODO: Ensure the user has the right to start this process
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
                process_config=process_config,
            )

        return send_event

    @staticmethod
    def _create_form_post_endpoint(
        input_type: type[BaseModel],
        process_class: str,
        process_id: str,
        process_controller: ProcessController,
        input_specs: HumanInSpecs | ProgramInSpecs,
        process_config: ProcessConfig,  # Unused parameter, but kept for consistency with the start endpoint
    ):
        """Create an endpoint to submit a form for continuing a process."""

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
            # TODO: Ensure the user has the right to continue this process
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
