import asyncio
from asyncio import sleep

from bson import ObjectId
from cachetools import TTLCache
from nats.aio.client import Client as NATS
from fastapi import HTTPException

from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import DiscoveryRequestEvent
from aihub_lib.nats.events.discovery import ProcessDiscoveryResponseEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.process.ProcessNCSubscriber import ProcessNCSubscriber
from aihub_lib.nats.topic_managers.process.ProcessInstanceTopicManager import ProcessInstanceTopicManager
from aihub_lib.nats.topic_managers.process.ProcessTopicManager import ProcessTopicManager
from aihub_lib.nats.topics import ProcessDiscoveryTopic
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity

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
            return ProcessDTO.from_entity(process, t)

    @staticmethod
    async def get_processes(nc: NATS, t: LocaleHandler) -> list[ProcessDTO]:
        """
        Returns both processes that are online (answer to a discovery broadcast) and processes
        that are saved in the database.
        """
        discovered_processes = await ProcessService.discover_processes(nc, t)
        saved_processes = [ProcessDTO.from_entity(process, t) for process in ProcessEntity.get_processes()]

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
                    is_online=True,
                )
                ProcessEntity.create_or_update_from_dto(process_dto)
                unique_processes_dict[unique_key] = process_dto

        processes = list(unique_processes_dict.values())

        if len(processes) > 0:
            DISCOVER_PROCESS_CACHE[cache_key] = processes

        return processes