import time
from typing import Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.distributor.events.ExternalProcessEvent import ExternalProcessEvent
from aihub_lib.nats.distributor.ExternalProcessEventDistributor import ExternalProcessEventDistributor
from aihub_lib.nats.events import ProcessStartEvent, WorkEvent
from aihub_lib.nats.events.discovery.process.ProcessConfigSpecs import ProcessConfigSpecs
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.messaging.entities.PersistedProcessEventEntity import PersistedProcessEventEntity
from aihub_lib.persistence.process.ProcessClassEntity import ProcessClassEntity
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from bson import ObjectId
from fastapi import HTTPException
from pydantic import ValidationError

from aihub_api.routes.process.dto import (
    AgentProcessStepDTO,
    HumanProcessStepDTO,
    PersistedEventDTO,
    ProgramProcessStepDTO,
)
from aihub_api.routes.process.dto.CreateProcessInstanceRequest import CreateProcessInstanceRequest
from aihub_api.routes.process.dto.FullProcessInstanceDTO import FullProcessInstanceDTO
from aihub_api.routes.process.dto.in_specs.HumanInDTO import HumanInDTO
from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessWalkthroughDTO import ProcessWalkthroughDTO
from aihub_api.routes.process.dto.SubmittedFormDTO import SubmittedFormDTO
from aihub_api.services.ModelCreationService import ModelCreationService


def _normalize_empty_objects_to_none(value: Any) -> Any:
    """Recursively normalize empty dicts/objects from FormKit to None."""
    if value is None:
        return None
    if isinstance(value, dict):
        if not value:
            return None
        return {k: _normalize_empty_objects_to_none(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_empty_objects_to_none(item) for item in value]
    return value


def _normalize_empty_locale_strings(value: Any) -> Any:
    """Recursively normalize empty LocaleString data from FormKit to None."""
    if value is None:
        return None
    if isinstance(value, dict):
        locale_keys = {"de", "en", "fr", "it"}
        if set(value.keys()).issubset(locale_keys):
            if not value or all(not val for val in value.values()):
                return None
        return {k: _normalize_empty_locale_strings(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_empty_locale_strings(item) for item in value]
    return value


class ProcessService:
    """
    Provides functionality to manage process classes and instances.
    Uses a database-first approach: process metadata is persisted by the discovery service
    and queried directly from the database rather than via NATS broadcasts.

    Users mainly interact with an agentic process through forms. Hence, the service offers methods to retrieve
    the formkit definitions of forms that the user can submit to either start a new process or continue
    an existing one.
    """

    # ==================== Form Interaction Methods ====================

    @staticmethod
    @trace_fn
    async def get_process_start_forms(process_class: str, process_id: str, t: LocaleHandler) -> list[HumanInDTO]:
        """Returns a list of formkit forms that the user can submit to start the process."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        return [HumanInDTO.from_human_in_specs(specs.to_specs(), t) for specs in class_entity.human_inputs]

    @staticmethod
    @trace_fn
    async def get_process_open_forms(
        process_class: str, process_id: str, process_walkthrough_id: str, t: LocaleHandler
    ) -> list[HumanInDTO]:
        """Returns a list of formkit forms that the user can submit to continue the given process walkthrough."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        human_inputs_specs = [specs.to_specs() for specs in class_entity.human_inputs]
        process_human_input_dtos: list[HumanInDTO] = []

        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(
            process_class, process_id, process_walkthrough_id
        )

        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                human_in_specs = next(
                    (
                        human_in
                        for human_in in human_inputs_specs
                        if human_in.event_specs.event_name == work_form["_event_name"]
                    ),
                    None,
                )
                if not human_in_specs:
                    continue

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
                    name=t.extract(human_in_specs.name),
                    description=t.extract(human_in_specs.description),
                    route=human_in_specs.route,
                    method=human_in_specs.method,
                    form=work_form_elements,
                    is_process_start=False,
                    event_specs=human_in_specs.event_specs,
                )
                process_human_input_dto.form = [
                    form_element.in_locale(t) for form_element in process_human_input_dto.form
                ]
                process_human_input_dtos.append(process_human_input_dto)

        return process_human_input_dtos

    @staticmethod
    @trace_fn
    async def submit_process_start_form(
        process_class: str,
        process_id: str,
        route: str,
        method: str,
        raw_event_data: dict,
        external_process_event_distributor: ExternalProcessEventDistributor,
        user: UserIdentity,
        t: LocaleHandler,
        process_config: ProcessConfig,
    ) -> SubmittedFormDTO:
        """Submit an object satisfying a form to start a process."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        human_inputs_specs = [specs.to_specs() for specs in class_entity.human_inputs]
        human_in = next(
            (human_in for human_in in human_inputs_specs if human_in.route == route and human_in.method == method),
            None,
        )

        if not human_in:
            raise ValueError(f"No human input found for route {route} and method {method}")

        event: ProcessStartEvent = ProcessStartEvent.from_raw_data(
            raw_event_data=raw_event_data, human_in=human_in, process_config=process_config
        )

        external_event: ExternalProcessEvent = await ProcessService._send_event(
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
    @trace_fn
    async def submit_process_open_form(
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
        """Submit an object satisfying a form to continue a process walkthrough."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        human_inputs_specs = [specs.to_specs() for specs in class_entity.human_inputs]
        persisted_events = PersistedProcessEventEntity.get_open_human_work_requests(
            process_class, process_id, process_walkthrough_id
        )

        human_in = None
        in_response_to = None
        for persisted_event in persisted_events:
            for work_form in persisted_event["event_data"]["forms"]:
                potential_human_in = next(
                    (
                        human_in
                        for human_in in human_inputs_specs
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

        event: WorkEvent = WorkEvent.deserialize_event(json_data)

        external_event: ExternalProcessEvent = await ProcessService._send_event(
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
    async def _send_event(
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

    # ==================== RPC Methods ====================

    @staticmethod
    @trace_fn
    async def get_process_configuration(process_class: str, process_id: str) -> dict[str, Any]:
        """
        Retrieve the current configuration data for a specific process instance.
        Returns empty dict if no configuration has been saved.
        """
        config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
        if config_entity and config_entity.config_data:
            return config_entity.config_data
        return {}

    # ==================== DB-first CRUD Methods ====================

    @staticmethod
    @trace_fn
    async def get_process_classes(t: LocaleHandler, online: bool | None = None) -> list[ProcessClassDTO]:
        """Returns all process classes from the database."""
        process_classes = []
        for class_entity in ProcessClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue
            process_classes.append(ProcessClassDTO.from_entity(class_entity, t))
        return process_classes

    @staticmethod
    @trace_fn
    async def get_process_class(process_class: str, t: LocaleHandler) -> ProcessClassDTO:
        """Returns a specific process class from the database."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")
        return ProcessClassDTO.from_entity(class_entity, t)

    @staticmethod
    @trace_fn
    async def get_process_class_instances(process_class: str, t: LocaleHandler) -> list[FullProcessInstanceDTO]:
        """Returns all instances of a specific process class from the database."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        instances = []
        configs = ProcessConfigEntityDocument.find_for_class(process_class)
        for config_entity in configs:
            instances.append(FullProcessInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return instances

    @staticmethod
    @trace_fn
    async def get_process_instance(process_class: str, process_id: str, t: LocaleHandler) -> FullProcessInstanceDTO:
        """Returns details for a given process instance from the database."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
        if config_entity is None:
            raise HTTPException(status_code=404, detail=f"Process instance {process_class}/{process_id} not found.")

        return FullProcessInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def create_process_instance(
        process_class: str,
        request: CreateProcessInstanceRequest,
        t: LocaleHandler,
    ) -> FullProcessInstanceDTO:
        """Creates a new process instance from an existing process class."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Process class '{process_class}' not found.")

        if not class_entity.is_online:
            raise HTTPException(
                status_code=503,
                detail=f"Process class '{process_class}' is not online. Make sure the process is running.",
            )

        existing_config = ProcessConfigEntityDocument.find_for_class_and_id(process_class, request.process_id)
        if existing_config:
            raise HTTPException(
                status_code=409, detail=f"Process instance '{process_class}/{request.process_id}' already exists."
            )

        # Normalize and validate configuration
        config = _normalize_empty_objects_to_none(request.configuration)
        config = _normalize_empty_locale_strings(config) or {}

        config_model = ModelCreationService.create_process_config_model(
            ProcessConfigSpecs(
                process_class=class_entity.process_config_specs.process_class
                if class_entity.process_config_specs
                else process_class,
                process_config_schema=class_entity.process_config_specs.process_config_schema
                if class_entity.process_config_specs
                else {},
            )
        )
        try:
            config_instance = config_model.model_validate(config)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_messages.append(f"{field_path}: {error['msg']}")
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {'; '.join(error_messages)}")

        name = config_instance.name if hasattr(config_instance, "name") and config_instance.name else None
        description = (
            config_instance.description
            if hasattr(config_instance, "description") and config_instance.description
            else None
        )
        icon = (
            config_instance.icon
            if hasattr(config_instance, "icon") and config_instance.icon
            else class_entity.icon or "mage:broadcast"
        )

        name_entity = (
            LocaleStringEntity.from_locale_string(name)
            if name
            else LocaleStringEntity(
                de=f"New {process_class}",
                en=f"New {process_class}",
                fr=f"Nouveau {process_class}",
                it=f"Nuovo {process_class}",
            )
        )
        description_entity = (
            LocaleStringEntity.from_locale_string(description)
            if description
            else LocaleStringEntity(de="", en="", fr="", it="")
        )

        full_config_data = {
            **config,
            "process_class": process_class,
            "process_id": request.process_id,
        }

        config_entity = ProcessConfigEntityDocument(
            process_class=process_class,
            process_id=request.process_id,
            name=name_entity,
            description=description_entity,
            icon=icon,
            config_data=full_config_data,
        )
        config_entity.save()

        return FullProcessInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def update_process_instance(
        process_class: str, process_id: str, configuration: dict[str, Any]
    ) -> dict[str, Any]:
        """Update the configuration data for a specific process instance."""
        class_entity = ProcessClassEntity.get_by_process_class(process_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Process class {process_class} not found.")

        config_entity = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
        if not config_entity:
            raise HTTPException(status_code=404, detail=f"Process instance {process_class}/{process_id} not found.")

        # Filter out FormKit internal fields
        configuration = {k: v for k, v in configuration.items() if not k.startswith("_")}

        # Normalize configuration before validation
        configuration = _normalize_empty_objects_to_none(configuration)
        configuration = _normalize_empty_locale_strings(configuration)

        config_model = ModelCreationService.create_process_config_model(
            ProcessConfigSpecs(
                process_class=class_entity.process_config_specs.process_class
                if class_entity.process_config_specs
                else process_class,
                process_config_schema=class_entity.process_config_specs.process_config_schema
                if class_entity.process_config_specs
                else {},
            )
        )
        try:
            config_instance = config_model.model_validate(configuration)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {e.errors()}")

        if hasattr(config_instance, "name") and config_instance.name:
            config_entity.name = LocaleStringEntity.from_locale_string(config_instance.name)

        if hasattr(config_instance, "description") and config_instance.description:
            config_entity.description = LocaleStringEntity.from_locale_string(config_instance.description)

        if hasattr(config_instance, "icon") and config_instance.icon:
            config_entity.icon = config_instance.icon

        config_entity.config_data = configuration
        config_entity.save()

        return configuration

    @staticmethod
    @trace_fn
    async def delete_process_instance(process_class: str, process_id: str) -> None:
        """Deletes a process instance by removing its configuration from the database."""
        config = ProcessConfigEntityDocument.find_for_class_and_id(process_class, process_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Process instance '{process_class}/{process_id}' not found.")

        ProcessConfigEntityDocument.delete_if_exists_for_class_and_id(process_class, process_id)

    @staticmethod
    @trace_fn
    async def get_all_process_instances(t: LocaleHandler, online: bool | None = None) -> list[FullProcessInstanceDTO]:
        """Returns all registered process instances from the database."""
        instances = []
        for class_entity in ProcessClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue

            configs = ProcessConfigEntityDocument.find_for_class(class_entity.process_class)
            for config_entity in configs:
                instances.append(FullProcessInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return instances

    # ==================== Walkthrough Methods ====================

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

            involved_agents, involved_humans = ProcessService._extract_involved_entities(walkthrough_data["events"], t)

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
    def _build_process_steps_from_events(
        events: list[dict], t: LocaleHandler, process_class: str, process_id: str
    ) -> list:
        """
        Builds a list of ProcessStepDTO objects from raw event data by pairing
        work requests with their corresponding work responses.
        """
        persisted_events = []
        for event in events:
            # Ensure process fields are present (they should be from the aggregation pipeline)
            if "process_class" not in event:
                event["process_class"] = process_class
            if "process_id" not in event:
                event["process_id"] = process_id
            if "process_walkthrough_id" not in event:
                event["process_walkthrough_id"] = ""

            persisted_events.append(PersistedEventDTO.model_validate(event))

        # Separate work request and work response events
        work_requests = []
        work_responses = []

        for persisted_event in persisted_events:
            if any("WorkRequestEvent" in parent for parent in persisted_event.event_parents):
                work_requests.append(persisted_event)
            elif any("WorkEvent" in parent for parent in persisted_event.event_parents):
                work_responses.append(persisted_event)

        # Sort by creation time
        work_requests.sort(key=lambda x: x.event_data.get("created_at", 0))
        work_responses.sort(key=lambda x: x.event_data.get("created_at", 0))

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

            step: HumanProcessStepDTO | AgentProcessStepDTO | ProgramProcessStepDTO
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

            standalone_step: HumanProcessStepDTO | AgentProcessStepDTO | ProgramProcessStepDTO
            if response_type == "human":
                standalone_step = HumanProcessStepDTO.from_events(None, response_event, step_index, t)
            elif response_type == "agent":
                standalone_step = AgentProcessStepDTO.from_events(None, response_event, step_index, t)
            else:  # program
                standalone_step = ProgramProcessStepDTO.from_events(None, response_event, step_index, t)

            steps.append(standalone_step)
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
        from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
        from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
        from aihub_lib.persistence.user.UserEntity import UserEntity

        from aihub_api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO
        from aihub_api.routes.user.dto.MinimalUserDTO import MinimalUserDTO

        involved_agents = {}  # Use dict to avoid duplicates by agent_id
        involved_humans = {}  # Use dict to avoid duplicates by user_id

        for event in events:
            event_data = event.get("event_data", {})
            event_parents = event.get("event_parents", [])

            if any("WorkEvent" in parent and "WorkRequestEvent" not in parent for parent in event_parents):
                if any("AgentWork" in parent for parent in event_parents):
                    agent_class = event_data["submitted_by"]["agent_class"]
                    agent_id = event_data["submitted_by"]["agent_id"]
                    agent_key = f"{agent_class}:{agent_id}"
                    if agent_key not in involved_agents:
                        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
                        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
                        if class_entity and config_entity:
                            involved_agents[agent_key] = MinimalAgentInstanceDTO.from_class_and_config(
                                class_entity, config_entity, t
                            )

                elif any("HumanWork" in parent for parent in event_parents):
                    submitted_by = event_data["submitted_by"]
                    user_id = (
                        submitted_by.get("id") if isinstance(submitted_by, dict) else getattr(submitted_by, "id", None)
                    )
                    if user_id and user_id not in involved_humans:
                        profile_image = (
                            submitted_by.get("profile_image")
                            if isinstance(submitted_by, dict)
                            else getattr(submitted_by, "profile_image", None)
                        )

                        if not profile_image:
                            try:
                                user_entity = UserEntity.by_oid(user_id)
                                involved_humans[user_id] = MinimalUserDTO.from_user_entity(user_entity)
                            except Exception:
                                pass
                        else:
                            involved_humans[user_id] = MinimalUserDTO.model_validate(
                                {
                                    "id": user_id,
                                    "name": (
                                        submitted_by.get("name")
                                        if isinstance(submitted_by, dict)
                                        else getattr(submitted_by, "name", "")
                                    ),
                                    "email": (
                                        submitted_by.get("email")
                                        if isinstance(submitted_by, dict)
                                        else getattr(submitted_by, "email", "")
                                    ),
                                    "profile_image": profile_image,
                                }
                            )

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
