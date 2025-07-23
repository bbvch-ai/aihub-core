import asyncio
import time
from asyncio import sleep
from typing import Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalProcessEvent import ExternalProcessEvent
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events import WorkEvent
from aihub_lib.nats.events.discovery import ProcessClassDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics.discovery.process.ProcessClassDiscoveryTopic import ProcessClassDiscoveryTopic
from aihub_lib.persistence.messaging.entities.PersistedProcessEventEntity import PersistedProcessEventEntity
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.dto.ProcessHumanInDto import ProcessHumanInDto
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO

# In-memory caches to avoid repeatedly querying NATS for process info
DISCOVER_PROCESSES_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache the entire process list for 60s
GET_PROCESS_INSTANCE_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual processes for 60s
GET_PROCESS_CLASS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache process classes for 60s


class ProcessService:
    """
    Provides functionality to discover and retrieve process information via NATS-based discovery events.
    `ProcessService` acts as the business logic layer for process operations,
    isolating NATS-based discovery requests from the HTTP layer.

    Users mainly interact with an agentic process through forms. Hence, the service offers methods to retrieve
    the formkit definitions of forms that the user can submit to either start a new process or continue
    an existing one.
    """

    @staticmethod
    async def get_process(nc: NATS, process_class: str, process_id: str, t: LocaleHandler) -> ProcessDTO:
        """
        Returns details for a given process. If process is online, use live information reported by the process,
        otherwise, use saved information from the database.
        """
        try:
            discovered_process = await ProcessService.discover_process_instance(nc, process_class, process_id)
            return ProcessDTO.from_instance(discovered_process, is_online=True, t=t)
        except HTTPException:
            process = ProcessEntity.get_process(process_class, process_id)
            if process is None:
                raise HTTPException(status_code=404, detail=f"Process {process_class}.{process_id} not found.")
            return ProcessDTO.from_entity(process, t, is_online=False)

    @staticmethod
    async def get_processes(nc: NATS, t: LocaleHandler) -> list[ProcessDTO]:
        """
        Returns both processes that are online (answer to a discovery broadcast) and processes
        that are saved in the database.
        """
        discovered_processes = await ProcessService.discover_processes(nc, t)
        saved_processes = [
            ProcessDTO.from_entity(process, t, is_online=False) for process in ProcessEntity.get_processes()
        ]

        all_processes = discovered_processes.copy()
        for saved_process in saved_processes:
            was_discovered = (
                len(
                    [
                        a
                        for a in discovered_processes
                        if a.process_id == saved_process.process_id and a.process_class == saved_process.process_class
                    ]
                )
                > 0
            )
            if not was_discovered:
                all_processes.append(saved_process)

        return all_processes

    @staticmethod
    async def discover_process_instance(nc: NATS, process_class: str, process_id: str) -> ProcessInstanceDTO:
        cache_key = (process_class, process_id)

        if cache_key in GET_PROCESS_INSTANCE_CACHE:
            return GET_PROCESS_INSTANCE_CACHE[cache_key]

        process_class_dto = await ProcessService.discover_process_class(nc, process_class)

        configs = ProcessConfigEntityDocument.find_for_class(process_class)
        for config in configs:
            if config.process_id == process_id:
                process_config = ProcessConfig.from_entity(config)
                process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                    class_dto=process_class_dto,
                    process_config=process_config,
                )
                GET_PROCESS_INSTANCE_CACHE[cache_key] = process_instance_dto
                return process_instance_dto

        if process_class_dto.default_process_config.process_id == process_id:
            process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                class_dto=process_class_dto,
                process_config=process_class_dto.default_process_config,
            )
            GET_PROCESS_INSTANCE_CACHE[cache_key] = process_instance_dto
            return process_instance_dto

        raise HTTPException(status_code=404, detail=f"Process {process_class}.{process_id} not found.")

    @staticmethod
    async def discover_process_instances_by_class(nc: NATS, process_class: str) -> list[ProcessInstanceDTO]:
        cache_key = (process_class, "*")

        if cache_key in GET_PROCESS_INSTANCE_CACHE:
            return GET_PROCESS_INSTANCE_CACHE[cache_key]

        process_class_dto = await ProcessService.discover_process_class(nc, process_class)

        configs = ProcessConfigEntityDocument.find_for_class(process_class)
        process_instance_dtos = []
        for config in configs:
            process_config = ProcessConfig.from_entity(config)
            process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                class_dto=process_class_dto,
                process_config=process_config,
            )
            process_instance_dtos.append(process_instance_dto)

        db_process_ids = {config.process_id for config in configs}

        if process_class_dto.default_process_config.process_id not in db_process_ids:
            process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                class_dto=process_class_dto,
                process_config=process_class_dto.default_process_config,
            )
            process_instance_dtos.append(process_instance_dto)

        if len(process_instance_dtos) > 0:
            GET_PROCESS_INSTANCE_CACHE[cache_key] = process_instance_dtos
            return process_instance_dtos

        raise HTTPException(status_code=404, detail=f"No process instances found for class {process_class}.")

    @staticmethod
    async def discover_process_class(nc: NATS, process_class: str) -> ProcessClassDTO:
        cache_key = process_class

        if cache_key in GET_PROCESS_CLASS_CACHE:
            return GET_PROCESS_CLASS_CACHE[cache_key]

        call_id = str(ObjectId())
        process_class_dto: ProcessClassDTO | None = None
        process_found_event = asyncio.Event()

        async def discovery_handler(event: ProcessClassDiscoveryResponseEvent, topic: ProcessClassDiscoveryTopic):
            nonlocal process_class_dto
            # Found the process, stop subscriber and signal event
            await nc_subscriber.stop()
            process_class_dto = ProcessClassDTO.from_discovery_event(event)
            process_found_event.set()

        topic_manager = ProcessClassTopicManager(process_class=process_class)
        nc_publisher = NCPublisher(nc)
        nc_subscriber = ProcessNCSubscriber.for_process_class_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Send discovery request for the specific process
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=topic_manager.get_process_class_discovery_subject_request(call_id=call_id),
        )

        # Wait up to 1 second for response
        try:
            await asyncio.wait_for(process_found_event.wait(), timeout=1.0)
        except TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Process {process_class} not found.")

        if process_class_dto is not None:
            GET_PROCESS_CLASS_CACHE[cache_key] = process_class_dto
            return process_class_dto

        raise HTTPException(status_code=404, detail=f"Process {process_class} not found.")

    @staticmethod
    async def discover_process_instances(nc: NATS) -> list[ProcessInstanceDTO]:
        cache_key = "all_process_instances"

        if cache_key in DISCOVER_PROCESSES_CACHE:
            return DISCOVER_PROCESSES_CACHE[cache_key]

        # Step 1: Discover which process classes are online
        online_processes: list[ProcessClassDTO] = await ProcessService.discover_process_classes(nc)

        # Step 2: Get all configured process instances from database
        configured_processes = []
        for process in online_processes:
            process_class = process.process_class
            configs = ProcessConfigEntityDocument.find_for_class(process_class)
            for config in configs:
                config_instance = ProcessConfig.from_entity(config)
                process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                    class_dto=process,
                    process_config=config_instance,
                )
                process_instance_dto.create_or_update_process_entity()
                configured_processes.append(process_instance_dto)

            # Step 3: Check if default process config is present in database
            db_process_ids = {configured_process.process_id for configured_process in configured_processes}
            if process.default_process_config.process_id not in db_process_ids:
                process_instance_dto = ProcessInstanceDTO.from_class_and_config(
                    class_dto=process,
                    process_config=process.default_process_config,
                )
                process_instance_dto.create_or_update_process_entity()
                configured_processes.append(process_instance_dto)

        if len(configured_processes) > 0:
            DISCOVER_PROCESSES_CACHE[cache_key] = configured_processes

        return configured_processes

    @staticmethod
    async def discover_process_classes(nc: NATS) -> list[ProcessClassDTO]:
        cache_key = "all_process_classes"

        if cache_key in DISCOVER_PROCESSES_CACHE:
            return DISCOVER_PROCESSES_CACHE[cache_key]

        call_id = str(ObjectId())
        discovery_responses: list[ProcessClassDiscoveryResponseEvent] = []

        async def discovery_handler(event: ProcessClassDiscoveryResponseEvent, topic: ProcessClassDiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = ProcessTopicManager()
        nc_publisher = NCPublisher(nc)
        nc_subscriber = ProcessNCSubscriber.for_process_class_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=topic_manager.get_process_class_discovery_subject_request(call_id=call_id),
        )

        # Wait briefly for responses
        await sleep(1)
        await nc_subscriber.stop()

        unique_processes_dict: dict[str, ProcessClassDTO] = {}

        for response in discovery_responses:
            unique_key = response.process_class

            if unique_key not in unique_processes_dict:
                process_class_dto = ProcessClassDTO.from_discovery_event(response)
                unique_processes_dict[unique_key] = process_class_dto

        processes = list(unique_processes_dict.values())

        if len(processes) > 0:
            DISCOVER_PROCESSES_CACHE[cache_key] = processes

        return processes

    @staticmethod
    async def discover_processes(nc: NATS, t: LocaleHandler) -> list[ProcessDTO]:
        discovered_processes = await ProcessService.discover_process_instances(nc)
        return [
            ProcessDTO.from_instance(process_instance, is_online=True, t=t) for process_instance in discovered_processes
        ]

    @staticmethod
    async def send_event(
        external_process_event_distributor: ExternalProcessEventDistributor,
        user: UserIdentity,
        work_event: WorkEvent,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str | None = None,
    ) -> ExternalProcessEvent:
        """Submits a piece of work from either a program or a human to a process."""
        external_event = ExternalProcessEvent(
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            event=work_event,
        )
        await external_process_event_distributor.distribute_event(external_event, user)
        return external_event

    @staticmethod
    async def get_process_start_forms(
        nc: NATS, process_class: str, process_id: str, t: LocaleHandler
    ) -> list[ProcessHumanInDto]:
        """Returns a list of formkit forms that the user can submit to start the process."""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        process_human_input_dtos: list[ProcessHumanInDto] = []

        for human_input in process.human_inputs:
            if not human_input.is_process_start:
                continue

            process_human_input_dto = ProcessHumanInDto(
                name=t.extract(human_input.name),
                description=t.extract(human_input.description),
                route=human_input.route,
                method=human_input.method,
                form=human_input.form,
            )
            process_human_input_dto.form = [form_element.in_locale(t) for form_element in process_human_input_dto.form]
            process_human_input_dtos.append(process_human_input_dto)
        return process_human_input_dtos

    @staticmethod
    async def get_process_open_forms(
        nc: NATS, process_class: str, process_id: str, process_walkthrough_id: str, t: LocaleHandler
    ) -> list[ProcessHumanInDto]:
        """Returns a list of formkit forms that the user can submit to continue the given process walkthrough"""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        process_human_input_dtos: list[ProcessHumanInDto] = []

        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(
            process_class, process_id, process_walkthrough_id
        )

        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                human_in = next(
                    (
                        human_in
                        for human_in in process.human_inputs
                        if human_in.event_specs.event_name == work_form["_event_name"]
                    ),
                    None,
                )
                work_form_elements: list[dict] = []

                for key, value in work_form.items():
                    if isinstance(value, dict) and value.get("is_formkit_element"):
                        work_form_elements.append(
                            {
                                **value,
                                "name": key,
                            }
                        )

                process_human_input_dto = ProcessHumanInDto(
                    name=t.extract(human_in.name),
                    description=t.extract(human_in.description),
                    route=human_in.route,
                    method=human_in.method,
                    form=work_form_elements,
                )
                process_human_input_dto.form = [
                    form_element.in_locale(t) for form_element in process_human_input_dto.form
                ]
                process_human_input_dtos.append(process_human_input_dto)

        return process_human_input_dtos

    @staticmethod
    async def submit_process_start_form(
        nc: NATS,
        process_class: str,
        process_id: str,
        route: str,
        method: str,
        raw_event_data: dict,
        external_process_event_distributor: ExternalProcessEventDistributor,
        user: UserIdentity,
        t: LocaleHandler,
    ) -> SubmittedFormDTO:
        """Submit an object satisfying a form to start a process"""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        human_in = next(
            (human_in for human_in in process.human_inputs if human_in.route == route and human_in.method == method),
            None,
        )

        if not human_in:
            raise ValueError(f"No human input found for route {route} and method {method}")

        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_event_name": human_in.event_specs.event_name,
            "_parent_event_names": human_in.event_specs.event_parents,
        }
        event: WorkEvent = WorkEvent.deserialize_event(json_data)

        external_event = await ProcessService.send_event(
            external_process_event_distributor,
            user,
            event,
            process_class,
            process_id,
        )
        return SubmittedFormDTO(
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=external_event.process_walkthrough_id,
        )

    @staticmethod
    async def submit_process_open_form(
        nc: NATS,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str,
        route: str,
        method: str,
        raw_event_data: dict,
        external_process_event_distributor: ExternalProcessEventDistributor,
        user: UserIdentity,
        t: LocaleHandler,
    ) -> SubmittedFormDTO:
        """Submit an object satisfying a form to continue a process walkthrough"""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(
            process_class, process_id, process_walkthrough_id
        )

        human_in = None
        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                potential_human_in = next(
                    (
                        human_in
                        for human_in in process.human_inputs
                        if human_in.event_specs.event_name == work_form["_event_name"]
                    ),
                    None,
                )
                if potential_human_in:
                    human_in = potential_human_in
                    break

        if not human_in:
            raise ValueError(f"No human input found for route {route} and method {method}")

        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "_event_name": human_in.event_specs.event_name,
            "_parent_event_names": human_in.event_specs.event_parents,
        }

        # TODO: Catch if WorkEvent can not be created and safe partial object to DB
        event: WorkEvent = WorkEvent.deserialize_event(json_data)

        external_event = await ProcessService.send_event(
            external_process_event_distributor,
            user,
            event,
            process_class,
            process_id,
            process_walkthrough_id,
        )
        return SubmittedFormDTO(
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=external_event.process_walkthrough_id,
        )

    @staticmethod
    def clear_cache() -> None:
        """
        Clears the in-memory caches used for process discovery. Useful for testing purposes to ensure fresh discovery
        requests.
        """
        DISCOVER_PROCESSES_CACHE.clear()
        GET_PROCESS_INSTANCE_CACHE.clear()
        GET_PROCESS_CLASS_CACHE.clear()
