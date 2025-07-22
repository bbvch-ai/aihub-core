import asyncio
import time
from asyncio import sleep
from typing import Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalProcessEvent import ExternalProcessEvent
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events import WorkEvent
from aihub_lib.nats.events.discovery import ProcessDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
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

from aihub_api.routes.process.dto import PersistedEventDTO, HumanProcessStepDTO, \
    AgentProcessStepDTO, ProgramProcessStepDTO
from aihub_api.routes.process.dto.ProcessWalkthroughDTO import ProcessWalkthroughDTO
from aihub_api.routes.process.dto.in_specs.AgentInDTO import AgentInDTO
from aihub_api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from aihub_api.routes.process.dto.in_specs.ProgramInDTO import ProgramInDTO
from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO

# In-memory caches to avoid repeatedly querying NATS for process info
DISCOVER_PROCESS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache the entire process list for 60s
GET_PROCESS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual processes for 60s


class ProcessService:
    """
    The process service connects humans and programs to agentic processes, as well as offering methods to
    retrieve the available processes and their current state.

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
                human_inputs=[HumanInDTO.from_human_in_specs(spec, t) for spec in event.human_inputs],
                program_inputs=[ProgramInDTO.from_program_in_specs(spec) for spec in event.program_inputs],
                agent_inputs=[AgentInDTO.from_agent_in_specs(spec, t) for spec in event.agent_inputs],
                is_online=True,
            )
            ProcessEntity.create_or_update_from_discovery_response(event)
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
                    human_inputs=[HumanInDTO.from_human_in_specs(spec, t) for spec in response.human_inputs],
                    program_inputs=[ProgramInDTO.from_program_in_specs(spec) for spec in response.program_inputs],
                    agent_inputs=[AgentInDTO.from_agent_in_specs(spec, t) for spec in response.agent_inputs],
                    is_online=True,
                )
                ProcessEntity.create_or_update_from_discovery_response(response)
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
    ) -> list[HumanInDTO]:
        """Returns a list of formkit forms that the user can submit to start the process."""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        return process.human_inputs

    @staticmethod
    async def get_process_open_forms(
        nc: NATS, process_class: str, process_id: str, process_walkthrough_id: str, t: LocaleHandler
    ) -> list[HumanInDTO]:
        """Returns a list of formkit forms that the user can submit to continue the given process walkthrough"""
        process = await ProcessService.get_process(nc=nc, process_class=process_class, process_id=process_id, t=t)
        process_human_input_dtos: list[HumanInDTO] = []

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

                process_human_input_dto = HumanInDTO(
                    name=human_in.name,
                    description=human_in.description,
                    route=human_in.route,
                    method=human_in.method,
                    form=work_form_elements,
                    is_process_start=False,
                    event_specs=human_in.event_specs,
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

        # TODO: Ensure this also works for programs
        human_in = None
        in_response_to = None
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
                    in_response_to = persisted_event["event_id"]
                    break

        if not human_in:
            raise ValueError(f"No human input found for route {route} and method {method}")

        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            **raw_event_data,
            "in_response_to": in_response_to,
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
    async def get_process_walkthroughs(
        process_class: str, process_id: str, t: LocaleHandler, page: int = 1, page_size: int = 20
    ) -> tuple[int, list]:
        """
        Gets paginated process walkthroughs with detailed step information.
        Returns a tuple of (total_count, walkthroughs_with_steps).
        """
        total_count, walkthroughs_data = PersistedProcessEventEntity.get_paginated_walkthrough_events(
            process_class, process_id, page, page_size
        )

        walkthroughs = []
        for walkthrough_data in walkthroughs_data:
            process_steps = ProcessService._build_process_steps_from_events(
                walkthrough_data["events"], t, walkthrough_data["process_class"], walkthrough_data["process_id"]
            )

            completed_steps = sum(1 for step in process_steps if step.is_completed)
            
            # Determine if walkthrough is active by checking for ProcessStopEvent
            is_active = True
            for event in walkthrough_data["events"]:
                if any("ProcessStopEvent" in parent for parent in event.get("event_parents", [])):
                    is_active = False
                    break
            
            # Collect involved agents and humans
            involved_agents, involved_humans = ProcessService._extract_involved_entities(
                walkthrough_data["events"], t
            )

            walkthrough = ProcessWalkthroughDTO(
                process_walkthrough_id=walkthrough_data["process_walkthrough_id"],
                process_class=walkthrough_data["process_class"],
                process_id=walkthrough_data["process_id"],
                process_steps=process_steps,
                created_at=walkthrough_data["first_event_timestamp"],
                updated_at=walkthrough_data["last_event_timestamp"],
                total_steps=len(process_steps),
                completed_steps=completed_steps,
                is_active=is_active,
                involved_agents=involved_agents,
                involved_humans=involved_humans,
            )
            walkthroughs.append(walkthrough)

        return total_count, walkthroughs

    @staticmethod
    def _build_process_steps_from_events(events: list[dict], t: LocaleHandler, process_class: str, process_id: str) -> list:
        """
        Builds a list of ProcessStepDTO objects from raw event data by pairing
        work requests with their corresponding work responses.
        """
        # Convert raw events to Pydantic models for better typing
        persisted_events = []
        for event in events:
            # Ensure process fields are present (they should be from the aggregation pipeline)
            if "process_class" not in event:
                event["process_class"] = process_class
            if "process_id" not in event:
                event["process_id"] = process_id
            if "process_walkthrough_id" not in event:
                # This should not happen, but fallback to empty string if needed
                event["process_walkthrough_id"] = ""
            
            persisted_events.append(PersistedEventDTO(**event))

        # Separate work request and work response events
        work_requests = []
        work_responses = []

        for event in persisted_events:
            if any("WorkRequestEvent" in parent for parent in event.event_parents):
                work_requests.append(event)
            elif any("WorkEvent" in parent for parent in event.event_parents):
                work_responses.append(event)

        # Sort by creation time
        work_requests.sort(key=lambda x: x.event_data.get("created_at", 0))
        work_responses.sort(key=lambda x: x.event_data.get("created_at", 0))

        # Create steps from all events in chronological order
        steps = []
        step_index = 0
        used_response_ids = set()

        # First, create steps from work requests and their corresponding responses
        for request_event in work_requests:
            request_type = ProcessService._get_step_type_from_event_parents(request_event.event_parents)

            # Find corresponding work response using in_response_to field
            response_event = None
            for resp_event in work_responses:
                if resp_event.event_data.get("in_response_to") == request_event.event_id:
                    response_event = resp_event
                    used_response_ids.add(resp_event.event_id)
                    break

            # Create entity-specific step using classmethods
            if request_type == "human":
                step = HumanProcessStepDTO.from_events(request_event, response_event, step_index, t)
            elif request_type == "agent":
                step = AgentProcessStepDTO.from_events(request_event, response_event, step_index, t)
            else:  # program
                step = ProgramProcessStepDTO.from_events(request_event, response_event, step_index, t)

            steps.append(step)
            step_index += 1

        # Second, create steps from standalone work responses (process start events)
        standalone_responses = [resp for resp in work_responses if resp.event_id not in used_response_ids]
        for response_event in standalone_responses:
            response_type = ProcessService._get_step_type_from_event_parents(response_event.event_parents)

            # Create entity-specific step with no request event
            if response_type == "human":
                step = HumanProcessStepDTO.from_events(None, response_event, step_index, t)
            elif response_type == "agent":
                step = AgentProcessStepDTO.from_events(None, response_event, step_index, t)
            else:  # program
                step = ProgramProcessStepDTO.from_events(None, response_event, step_index, t)

            steps.append(step)
            step_index += 1

        # Sort all steps by creation time to ensure correct chronological order
        steps.sort(key=lambda x: x.created_at)
        
        # Re-index steps after sorting
        for i, step in enumerate(steps):
            step.step_index = i

        return steps

    @staticmethod
    def _extract_involved_entities(events: list[dict], t) -> tuple[list, list]:
        """
        Extracts involved agents and humans from events.
        Returns a tuple of (involved_agents, involved_humans).
        """
        from aihub_lib.persistence.agents.AgentEntity import AgentEntity
        from aihub_lib.persistence.user.UserEntity import UserEntity
        
        from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
        from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO

        involved_agents = {}  # Use dict to avoid duplicates by agent_id
        involved_humans = {}  # Use dict to avoid duplicates by user_id

        for event in events:
            event_data = event.get("event_data", {})
            event_parents = event.get("event_parents", [])
            
            # Check if this is a work event (response, not request)
            if any("WorkEvent" in parent and "WorkRequestEvent" not in parent for parent in event_parents):
                # Check for agent work
                if any("AgentWork" in parent for parent in event_parents):
                    agent_class = event_data.get("agent_class")
                    agent_id = event_data.get("agent_id")
                    if agent_class and agent_id:
                        agent_key = f"{agent_class}:{agent_id}"
                        if agent_key not in involved_agents:
                            try:
                                agent_entity = AgentEntity.get_agent(agent_class, agent_id)
                                if agent_entity:
                                    involved_agents[agent_key] = MinimalAgentDTO.from_entity(agent_entity, t)
                            except Exception:
                                pass  # Agent not found or error loading
                
                # Check for human work
                elif any("HumanWork" in parent for parent in event_parents):
                    submitted_by = event_data.get("submitted_by")
                    if submitted_by:
                        user_id = submitted_by.get("id") if isinstance(submitted_by, dict) else getattr(submitted_by, "id", None)
                        if user_id and user_id not in involved_humans:
                            try:
                                # Check if we need to fetch user profile
                                profile_image = None
                                if isinstance(submitted_by, dict):
                                    profile_image = submitted_by.get("profile_image")
                                else:
                                    profile_image = getattr(submitted_by, "profile_image", None)
                                
                                if not profile_image:
                                    # Fetch user from database to get profile image
                                    user_entity = UserEntity.get_user_by_id(user_id)
                                    if user_entity:
                                        involved_humans[user_id] = MinimalUserDTO.from_user_entity(user_entity)
                                else:
                                    # Use existing user data
                                    if isinstance(submitted_by, dict):
                                        involved_humans[user_id] = MinimalUserDTO(
                                            id=submitted_by.get("id", ""),
                                            name=submitted_by.get("name", ""),
                                            email=submitted_by.get("email", ""),
                                            profile_image=profile_image
                                        )
                                    else:
                                        involved_humans[user_id] = MinimalUserDTO(
                                            id=getattr(submitted_by, "id", ""),
                                            name=getattr(submitted_by, "name", ""),
                                            email=getattr(submitted_by, "email", ""),
                                            profile_image=profile_image
                                        )
                            except Exception:
                                pass  # User not found or error loading

        return list(involved_agents.values()), list(involved_humans.values())

    @staticmethod
    def _get_step_type_from_event_parents(event_parents: list[str]) -> str:
        """Determines the step type (human/agent/program) from the event parents."""
        for parent in event_parents:
            if "HumanWork" in parent:
                return "human"
            elif "AgentWork" in parent:
                return "agent"
            elif "ProgramWork" in parent:
                return "program"
        return "human"  # Default fallback

    @staticmethod
    def _events_match(request_event: dict, response_event: dict) -> bool:
        """
        Determines if a work request event matches a work response event.
        This is done by checking if the response event name matches any of the
        form event names in the request, or by other matching logic.
        """
        request_data = request_event.get("event_data", {})
        response_event_name = response_event.get("event_name", "")

        # For human work requests, check forms
        forms = request_data.get("forms", [])
        if forms:
            for form in forms:
                if form.get("_event_name") == response_event_name:
                    return True

        # For agent/program work requests, match by removing "Request" from the name
        request_name = request_event.get("event_name", "")
        expected_response_name = request_name.replace("RequestEvent", "Event").replace("Request", "")
        if response_event_name == expected_response_name:
            return True

        return False

