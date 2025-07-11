import asyncio
from typing import Any

import time
from asyncio import sleep

from aihub_api.routes.process.dto.ProcessHumanInputDto import ProcessHumanInputDto
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalProcessEvent import ExternalProcessEvent
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events import DiscoveryRequestEvent, WorkEvent
from aihub_lib.nats.events.discovery import ProcessDiscoveryResponseEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics import ProcessDiscoveryTopic
from aihub_lib.persistence.messaging.entities.PersistedProcessEventEntity import PersistedProcessEventEntity
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO

# In-memory caches to avoid repeatedly querying NATS for process info
DISCOVER_PROCESS_CACHE = TTLCache(maxsize=1, ttl=60)  # Cache the entire process list for 60s
GET_PROCESS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual processes for 60s


class ProcessService:
    @staticmethod
    async def get_process(nc: NATS, process_class: str, process_id: str, t: LocaleHandler) -> ProcessDTO:
        """
        Returns details for a given process. If process is online, use live information reported by the process,
        otherwise, use saved information from the database.
        """
        try:
            return await ProcessService.discover_process(nc, process_class, process_id, t)
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
    async def discover_process(nc: NATS, process_class: str, process_id: str, t: LocaleHandler) -> ProcessDTO:
        """
        Retrieves details about a specific process. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for a response.
        """
        cache_key = (process_class, process_id)

        if cache_key in GET_PROCESS_CACHE:
            return GET_PROCESS_CACHE[cache_key]

        call_id = str(ObjectId())
        process_dto: ProcessDTO | None = None
        process_found_event = asyncio.Event()

        async def discovery_handler(event: ProcessDiscoveryResponseEvent, topic: ProcessDiscoveryTopic):
            nonlocal process_dto
            # Found the process, stop subscriber and signal event
            await nc_subscriber.stop()
            process_dto = ProcessDTO(
                process_class=event.process_class,
                process_id=event.process_id,
                process_config=ProcessConfigDTO.from_process_config(event.process_config, t),
                human_inputs=event.human_inputs,
                program_inputs=event.program_inputs,
                agent_inputs=event.agent_inputs,
                is_online=True,
            )
            ProcessEntity.create_or_update_from_dto(process_dto)
            process_found_event.set()

        topic_manager = ProcessInstanceTopicManager(process_class=process_class, process_id=process_id)
        nc_publisher = NCPublisher(nc)
        nc_subscriber = ProcessNCSubscriber.for_process_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Send discovery request for the specific process
        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(), subject=topic_manager.get_process_discovery_subject_request(call_id=call_id)
        )

        # Wait up to 1 second for response
        try:
            await asyncio.wait_for(process_found_event.wait(), timeout=1.0)
        except TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Process {process_class}.{process_id} not found.")

        if process_dto is not None:
            GET_PROCESS_CACHE[cache_key] = process_dto
            return process_dto

        raise HTTPException(status_code=404, detail=f"Process {process_class}.{process_id} not found.")

    @staticmethod
    async def discover_processes(nc: NATS, t: LocaleHandler) -> list[ProcessDTO]:
        """
        Discovers all processes by broadcasting a discovery request and waiting for responses.
        Returns a cached result if available.
        """
        cache_key = "all_processes"

        if cache_key in DISCOVER_PROCESS_CACHE:
            return DISCOVER_PROCESS_CACHE[cache_key]

        call_id = str(ObjectId())
        discovery_responses = []

        async def discovery_handler(event: ProcessDiscoveryResponseEvent, topic: ProcessDiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = ProcessTopicManager()
        nc_publisher = NCPublisher(nc)
        nc_subscriber = ProcessNCSubscriber.for_process_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(), subject=topic_manager.get_process_discovery_subject_request(call_id=call_id)
        )

        # Wait briefly for responses
        await sleep(1)
        await nc_subscriber.stop()

        unique_processes_dict = {}

        for response in discovery_responses:
            unique_key = (response.process_class, response.process_id)

            if unique_key not in unique_processes_dict:
                process_dto = ProcessDTO(
                    process_class=response.process_class,
                    process_id=response.process_id,
                    process_config=ProcessConfigDTO.from_process_config(response.process_config, t),
                    human_inputs=response.human_inputs,
                    program_inputs=response.program_inputs,
                    agent_inputs=response.agent_inputs,
                    is_online=True,
                )
                ProcessEntity.create_or_update_from_dto(process_dto)
                unique_processes_dict[unique_key] = process_dto

        processes = list(unique_processes_dict.values())

        if len(processes) > 0:
            DISCOVER_PROCESS_CACHE[cache_key] = processes

        return processes

    @staticmethod
    async def send_event(
        external_process_event_distributor: ExternalProcessEventDistributor,
        user: UserIdentity,
        work_event: WorkEvent,
        process_class: str,
        process_id: str,
        process_walkthrough_id: str | None = None,
    ) -> bool:
        # TODO: Safe if it is only partial, and return False
        external_event = ExternalProcessEvent(
            process_class=process_class,
            process_id=process_id,
            process_walkthrough_id=process_walkthrough_id,
            event=work_event,
        )
        await external_process_event_distributor.distribute_event(external_event, user)
        return True

    @staticmethod
    async def get_process_start_forms(nc: NATS, process_class: str, process_id: str, t: LocaleHandler) -> list[ProcessHumanInputDto]:
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        process_human_input_dtos: list[ProcessHumanInputDto] = []

        for human_input in process.human_inputs:
            if not human_input.is_process_start:
                continue

            process_human_input_dto = ProcessHumanInputDto(
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
    async def get_process_open_forms(nc: NATS, process_class: str, process_id: str, process_walkthrough_id: str, t: LocaleHandler) -> list[ProcessHumanInputDto]:
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        process_human_input_dtos: list[ProcessHumanInputDto] = []

        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(process_class, process_id, process_walkthrough_id)

        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                human_in = next((human_in for human_in in process.human_inputs if human_in.event_specs.event_name == work_form["_event_name"]), None)
                work_form_elements: list[dict] = []

                for key, value in work_form.items():
                    if isinstance(value, dict) and value.get("is_formkit_element"):
                        work_form_elements.append({
                            "name": key,
                            **value,
                        })

                process_human_input_dto = ProcessHumanInputDto(
                    name=t.extract(human_in.name),
                    description=t.extract(human_in.description),
                    route=human_in.route,
                    method=human_in.method,
                    form=work_form_elements,
                )
                process_human_input_dto.form = [form_element.in_locale(t) for form_element in process_human_input_dto.form]
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
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        human_in = next((human_in for human_in in process.human_inputs if human_in.route == route and human_in.method == method), None)

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

        await ProcessService.send_event(
            external_process_event_distributor,
            user,
            event,
            process_class,
            process_id,
        )
        return SubmittedFormDTO()

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
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(process_class, process_id, process_walkthrough_id)

        human_in = None
        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                potential_human_in = next((human_in for human_in in process.human_inputs if human_in.event_specs.event_name == work_form["_event_name"]), None)
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
        event: WorkEvent = WorkEvent.deserialize_event(json_data)

        await ProcessService.send_event(
            external_process_event_distributor,
            user,
            event,
            process_class,
            process_id,
            process_walkthrough_id,
        )
        return SubmittedFormDTO()
