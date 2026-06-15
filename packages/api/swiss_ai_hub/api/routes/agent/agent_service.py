import asyncio
import logging
from collections.abc import Callable
from typing import Annotated, Any

from bson import ObjectId
from fastapi import HTTPException
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.distributor import ExternalAgentEvent, ExternalAgentEventDistributor
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import (
    AgentConfigSpecs,
    DisplayEvent,
    ExceptionEvent,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
    StopEvent,
)
from swiss_ai_hub.core.form import normalize_empty_locale_strings, normalize_empty_objects_to_none
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.agents import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.routes import ChatService, JsonResources, StreamingResources
from swiss_ai_hub.core.subscribers import AgentNCSubscriber
from swiss_ai_hub.core.topic_managers import AgentThreadTopicManager
from swiss_ai_hub.core.topics.agents import AgentInstanceTopic

from swiss_ai_hub.api.routes.agent.dto.agent_class_dto import AgentClassDTO
from swiss_ai_hub.api.routes.agent.dto.create_agent_instance_request import CreateAgentInstanceRequest
from swiss_ai_hub.api.routes.agent.dto.full_agent_instance_dto import FullAgentInstanceDTO
from swiss_ai_hub.api.routes.agent.dto.minimal_agent_instance_dto import MinimalAgentInstanceDTO
from swiss_ai_hub.api.routes.thread.dto.thread_dto import ThreadDTO
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.services.model_creation_service import ModelCreationService
from swiss_ai_hub.api.util.config_authorization_service import ConfigAuthorizationService
from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

logger = logging.getLogger(__name__)


class AgentService:
    """
    Provides functionality to retrieve and manage agent information from the database.
    Online status is determined by the AgentEndpointsDiscoveryService which periodically
    broadcasts NATS discovery requests and updates `last_discovered` timestamps.
    """

    @staticmethod
    @trace_fn
    def get_minimal_agent_instance(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentInstanceDTO:
        """Returns minimal details for an agent instance from database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class=agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent config {agent_class}/{agent_id} not found.")

        return MinimalAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def get_agent_instance(agent_class: str, agent_id: str, t: LocaleHandler) -> FullAgentInstanceDTO:
        """
        Returns details for a given agent instance from the database.
        Online status is derived from the last_discovered timestamp on the class entity.
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent instance {agent_class}/{agent_id} not found.")

        return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def get_all_agent_instances(
        t: LocaleHandler,
        online: bool | None = None,
        search: str | None = None,
        agent_class: str | None = None,
    ) -> list[FullAgentInstanceDTO]:
        """
        Returns all registered agent instances from the database.
        Online status is determined by the last_discovered timestamp - agents that responded
        to a discovery broadcast within AgentClassEntity.ONLINE_THRESHOLD are considered online.
        """
        agents = []
        for class_entity in AgentClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue
            if agent_class is not None and class_entity.agent_class != agent_class:
                continue

            configs = AgentConfigEntityDocument.find_for_name(agent_class=class_entity.agent_class, name=search)
            for config_entity in configs:
                agents.append(FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return agents

    @staticmethod
    async def _send_event(
        *,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        user: UserIdentity,
        input_event: BaseEvent,
        agent_class: str,
        agent_id: str,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent:
        """Sends an event to a specific agent."""
        if thread_id:
            thread = ThreadEntity.get_thread_by_id(str(thread_id))
        else:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
            )

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=str(thread.id),
            display_id=display_id or str(ObjectId()),
            run_id="*",
        )
        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=input_event,
        )
        resources: JsonResources = await ChatService.start_json_event_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            external_event=external_event,
            topic_manager=topic_manager,
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
        )

        await ChatService.wait_for_stop_then_drain(resources)

        return resources.stop_event

    @staticmethod
    @trace_fn
    async def send_agent_input_event(
        *,
        nc: NATS,
        agent_class: str,
        agent_id: str,
        input_event_parents: list[str],
        input_event_name: str,
        raw_event_data: dict,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None,
        display_id: ObjectId | None,
        user: UserIdentity,
        t: LocaleHandler,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent:
        """Sends an event (start or HITL response) to a specific agent and waits for a response."""
        event: StartEvent | HumanInTheLoopResponseEvent = expected_type.from_raw_data(
            raw_event_data=raw_event_data,
            user=user,
            start_event_name=input_event_name,
            start_event_parents=input_event_parents,
            t=t,
        )

        return await AgentService._send_event(
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
            user=user,
            input_event=event,
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            subscribe_to_thread=subscribe_to_thread,
        )

    @staticmethod
    @trace_fn
    async def send_agent_input_event_stream(
        *,
        nc: NATS,
        agent_class: str,
        agent_id: str,
        input_event_parents: list[str],
        input_event_name: str,
        raw_event_data: dict,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None,
        display_id: ObjectId | None,
        user: UserIdentity,
        t: LocaleHandler,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StreamingResources:
        """
        Sends an event (start or HITL response) to a specific agent and returns streaming resources for SSE.
        Yields ALL events (not just chunks) as raw events without conversion.
        """
        event: StartEvent | HumanInTheLoopResponseEvent = expected_type.from_raw_data(
            raw_event_data=raw_event_data,
            user=user,
            start_event_name=input_event_name,
            start_event_parents=input_event_parents,
            t=t,
        )

        if thread_id:
            thread = ThreadEntity.get_thread_by_id(str(thread_id))
        else:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
            )

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=str(thread.id),
            display_id=display_id or str(ObjectId()),
            run_id="*",
        )

        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=event,
        )

        stop_signal = asyncio.Event()
        event_queue: asyncio.Queue[DisplayEvent] = asyncio.Queue()

        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,
            chunk_queue=event_queue,
            stop_event=None,
        )

        async def event_handler(event: DisplayEvent, topic: AgentInstanceTopic):
            """Handles ALL events and puts them in the queue without conversion."""
            logger.debug(f"Received event for streaming: {event.event_name}")

            await event_queue.put(event)

            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id

            if event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stopping stream")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event.event_name}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_hitl_request_event:
                logger.debug(f"Received HITL request event: {event.event_name}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=event_handler,
            subscriber_name="AgentServiceSendAgentInputEventStream",
        )
        resources.subscriber = subscriber
        await subscriber.start()
        logger.debug(f"Subscriber created for streaming subject: {subscriber.subject}")

        await external_agent_event_distributor.distribute_event(external_event, user)

        return resources

    @staticmethod
    @trace_fn
    async def get_agent_instance_threads(
        *,
        agent_class: str,
        agent_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[int, list[ThreadDTO]]:
        """Retrieves a paginated list of threads that a specific agent instance is part of."""
        return await ThreadService.get_paginated_threads_for_agent(
            agent_class,
            agent_id,
            t=t,
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

    @staticmethod
    @trace_fn
    async def get_agent_configuration(agent_class: str, agent_id: str) -> dict[str, Any]:
        """
        Retrieve the current configuration data for a specific agent.
        Returns empty dict if no configuration has been saved.
        """
        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity and config_entity.config_data:
            return config_entity.config_data
        return {}

    @staticmethod
    @trace_fn
    async def update_agent_instance(
        agent_class: str, agent_id: str, configuration: dict[str, Any], t: LocaleHandler, *, user: UserIdentity
    ) -> dict[str, Any]:
        """
        Update the configuration data for a specific agent instance.
        Validates the configuration against the agent's schema before saving.
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if not config_entity:
            raise HTTPException(status_code=404, detail=f"Agent config {agent_class}/{agent_id} not found.")

        configuration = InstanceConfigHelper.normalize_form_configuration(configuration)

        config_model = ModelCreationService.create_agent_config_model(
            AgentConfigSpecs(
                agent_class=class_entity.agent_config_specs.agent_class,
                agent_config_schema=class_entity.agent_config_specs.agent_config_schema,
            )
        )
        config_instance = InstanceConfigHelper.validate_config_for_update(configuration, config_model)

        ConfigAuthorizationService.validate_config_authorization_or_raise(
            form_elements=class_entity.form,
            config=configuration,
            access_checker=AccessChecker.from_user(user),
            t=t,
        )

        config_entity = InstanceConfigHelper.apply_metadata_to_entity(config_instance, config_entity)

        config_entity.config_data = configuration
        config_entity.save()

        return configuration

    @staticmethod
    @trace_fn
    async def get_agent_classes(t: LocaleHandler, online: bool | None = None) -> list[AgentClassDTO]:
        """Returns all agent classes from the database."""
        agent_classes = []
        for class_entity in AgentClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue
            agent_classes.append(AgentClassDTO.from_entity(class_entity, t))
        return agent_classes

    @staticmethod
    @trace_fn
    async def get_agent_class(agent_class: str, t: LocaleHandler) -> AgentClassDTO:
        """Returns a specific agent class from the database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")
        return AgentClassDTO.from_entity(class_entity, t)

    @staticmethod
    @trace_fn
    async def get_agent_class_instances(agent_class: str, t: LocaleHandler) -> list[FullAgentInstanceDTO]:
        """Returns all instances of a specific agent class from the database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        instances = []
        configs = AgentConfigEntityDocument.find_for_class(agent_class)
        for config_entity in configs:
            instances.append(FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return instances

    @staticmethod
    @trace_fn
    async def create_agent_instance(
        agent_class: str,
        request: CreateAgentInstanceRequest,
        t: LocaleHandler,
        *,
        user: UserIdentity,
    ) -> FullAgentInstanceDTO:
        """
        Creates a new agent instance from an existing agent class.
        Requires the agent class to be online (i.e., the agent must be running).
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class '{agent_class}' not found.")

        if not class_entity.is_online:
            raise HTTPException(
                status_code=503,
                detail=f"Agent class '{agent_class}' is not online. Make sure the agent is running.",
            )

        existing_config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, request.agent_id)
        if existing_config:
            raise HTTPException(
                status_code=409, detail=f"Agent instance '{agent_class}/{request.agent_id}' already exists."
            )

        config = normalize_empty_objects_to_none(request.configuration)
        config = normalize_empty_locale_strings(config) or {}

        config_model = ModelCreationService.create_agent_config_model(
            AgentConfigSpecs(
                agent_class=class_entity.agent_config_specs.agent_class,
                agent_config_schema=class_entity.agent_config_specs.agent_config_schema,
            )
        )
        config_instance = InstanceConfigHelper.validate_config_for_create(config, config_model)

        ConfigAuthorizationService.validate_config_authorization_or_raise(
            form_elements=class_entity.form,
            config=config,
            access_checker=AccessChecker.from_user(user),
            t=t,
        )

        metadata = InstanceConfigHelper.extract_config_metadata(config_instance, class_entity.icon)
        locale = InstanceConfigHelper.build_locale_entities(
            metadata.name, metadata.description, agent_class, metadata.icon
        )

        full_config_data = {
            **config,
            "agent_class": agent_class,
            "agent_id": request.agent_id,
        }

        config_entity = AgentConfigEntityDocument(
            agent_class=agent_class,
            agent_id=request.agent_id,
            name=locale.name,
            description=locale.description,
            icon=locale.icon,
            config_data=full_config_data,
        )
        config_entity.save()

        if user.acting_within_tenant is not None:
            AgentService._grant_creator_access(agent_class, request.agent_id, user, config_entity)

        return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def delete_agent_instance(agent_class: str, agent_id: str) -> None:
        """Deletes an agent instance and the per-instance access it was granted on creation."""
        config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Agent instance '{agent_class}/{agent_id}' not found.")

        AgentConfigEntityDocument.delete_if_exists_for_class_and_id(agent_class, agent_id)

        rules = [
            AgentService._instance_user_rule(agent_class, agent_id),
            AgentService._instance_admin_rule(agent_class, agent_id),
        ]
        role_name = AgentService._instance_admin_role_name(agent_class, agent_id)
        AgentService._best_effort(
            lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants(rules), f"revoke {rules}"
        )
        AgentService._best_effort(
            lambda: RoleEntity.delete_role_from_all_tenants(role_name), f"delete role {role_name}"
        )

    @staticmethod
    def _instance_admin_rule(agent_class: str, agent_id: str) -> str:
        return f"aihub.admin.agent.{agent_class}.{agent_id}"

    @staticmethod
    def _instance_user_rule(agent_class: str, agent_id: str) -> str:
        return f"aihub.user.agent.{agent_class}.{agent_id}"

    @staticmethod
    def _instance_admin_role_name(agent_class: str, agent_id: str) -> str:
        return f"agent-{agent_class}-{agent_id}-admin"

    @staticmethod
    def _grant_creator_access(
        agent_class: str, agent_id: str, user: UserIdentity, config_entity: AgentConfigEntityDocument
    ) -> None:
        """Grants the creating tenant and creator per-instance admin access, rolling back on failure.

        Tenant ceiling gets the instance rule only when not already covered by a broader rule;
        the creator always receives a dedicated per-instance admin role.
        """
        tenant = user.acting_within_tenant
        admin_rule = AgentService._instance_admin_rule(agent_class, agent_id)
        role_name = AgentService._instance_admin_role_name(agent_class, agent_id)
        granted_tenant_rule = False
        created_role = False
        try:
            if not AccessChecker.rules_grant_admin_to_agent(tenant.access_rules, agent_class, agent_id):
                TenantMetadataEntity.grant_access_rule(tenant.id, admin_rule)
                granted_tenant_rule = True
            created_role = AgentService._ensure_instance_admin_role(
                role_name, admin_rule, tenant.id, agent_class, agent_id
            )
            UserTenantRoleEntity.add_roles(user.id, tenant.id, [role_name])
        except Exception as error:
            if created_role:
                AgentService._best_effort(
                    lambda: RoleEntity.delete_role_from_all_tenants(role_name), f"delete role {role_name}"
                )
            if granted_tenant_rule:
                AgentService._best_effort(
                    lambda: TenantMetadataEntity.revoke_access_rule_from_all_tenants([admin_rule]),
                    f"revoke {admin_rule}",
                )
            AgentService._best_effort(config_entity.delete, "delete config")
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Agent instance '{agent_class}/{agent_id}' was created but access could not be granted; "
                    "the creation was rolled back."
                ),
            ) from error

    @staticmethod
    def _best_effort(action: Callable[[], Any], description: str) -> None:
        """Runs a compensating/cleanup action, swallowing and logging any failure.

        Used for rollback and post-delete cleanup so a secondary failure never masks the
        primary outcome or aborts a delete whose instance is already gone.
        """
        try:
            action()
        except Exception:
            logger.exception("Best-effort step failed: %s", description)

    @staticmethod
    def _ensure_instance_admin_role(
        role_name: str, admin_rule: str, tenant_id: str, agent_class: str, agent_id: str
    ) -> bool:
        """Creates the per-instance admin role if absent. Returns whether it was created."""
        if RoleEntity.objects(name=role_name, tenant_id=tenant_id).first():
            return False
        RoleEntity.create_tenant_role(
            name=role_name,
            description=f"Admin access to agent instance {agent_class}/{agent_id}",
            access_rules=[admin_rule],
            tenant_id=tenant_id,
        )
        return True
