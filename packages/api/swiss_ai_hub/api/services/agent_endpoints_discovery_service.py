import asyncio
import hashlib
import logging
from asyncio import sleep
from functools import reduce
from operator import or_
from typing import Annotated, override

from bson import ObjectId
from fastapi import Body, Depends, FastAPI, HTTPException, Path, Query, Security
from mongoengine import DoesNotExist
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from redis.asyncio import Redis
from starlette.responses import StreamingResponse
from stringcase import snakecase
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.usage import (
    ResourceType,
    UsageLimitMessages,
    UsageLimits,
    use_usage_limits,
)
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.distributor import ExternalAgentEventDistributor, use_external_agent_event_distributor
from swiss_ai_hub.core.events import ClassDiscoveryRequestEvent, EventSpecs
from swiss_ai_hub.core.events.agent import (
    AgentClassDiscoveryResponseEvent,
    ExceptionEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import LangfuseProvisioner, OnlineAgent, OpenWebuiProvisioner
from swiss_ai_hub.core.persistence.agents import AgentClassEntity
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import AgentInstanceRef, ThreadEntity, User
from swiss_ai_hub.core.publishers import NCPublisher
from swiss_ai_hub.core.subscribers import AgentNCSubscriber
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.agent.dto.agent_class_dto import AgentClassDTO
from swiss_ai_hub.api.routes.agent.dto.full_agent_instance_dto import FullAgentInstanceDTO
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.services.endpoints_discovery_service import EndpointsDiscoveryService
from swiss_ai_hub.api.services.model_creation_service import ModelCreationService

logger = logging.getLogger(__name__)


class AgentEndpointsDiscoveryService(EndpointsDiscoveryService):
    """
    This service ensures that new agents in the system are automatically registered.
    This ensures that the API and the Agents are decoupled.

    It broadcasts NATS discovery requests to find online agents and:
    1. Updates their last_discovered timestamp (which determines online status)
    2. Registers/deregisters dynamic API endpoints for agent events
    """

    _AGENTS_HASH_KEY = "discovery:agents:hash"
    _AGENTS_HASH_TTL = 3600

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        controller: AgentController,
        locale_handler: LocaleHandler,
        redis: Redis,
        langfuse_provisioner: LangfuseProvisioner | None = None,
        openwebui_provisioner: OpenWebuiProvisioner | None = None,
        discovery_interval: int = 60,
    ):
        super().__init__(nc, api_app, controller, locale_handler, discovery_interval)
        self.controller: AgentController = controller
        self.topic_manager: AgentTopicManager = AgentTopicManager()
        self._redis = redis
        self._langfuse_provisioner = langfuse_provisioner
        self._openwebui_provisioner = openwebui_provisioner

    @override
    async def _discover_and_register(self):
        """
        Discovers agent classes via NATS broadcast and registers class-level endpoints.

        This method:
        1. Broadcasts a NATS discovery request to all running agents
        2. Collects responses and updates last_discovered timestamps in database
        3. Registers/deregisters dynamic API endpoints at the CLASS level (not instance level)

        Endpoints use {agent_id} as a FastAPI path parameter, with instance validation at request time.
        """
        # Step 1: Discover which agent classes are online via NATS broadcast
        discovered_classes: list[AgentClassDTO] = await self._broadcast_discovery()

        online_class_names = {dto.agent_class for dto in discovered_classes}

        # Step 2: Deregister endpoints for classes no longer online
        for agent_class in list(self.registered_classes):
            if agent_class not in online_class_names:
                self._deregister_endpoints_for_class(agent_class)

        self.app.openapi_schema = None

        # Step 3: Register endpoints for newly discovered classes
        for agent_class_dto in discovered_classes:
            if agent_class_dto.agent_class not in self.registered_classes:
                self._register_class_endpoints(
                    agent_class=agent_class_dto.agent_class,
                    start_events=agent_class_dto.start_events,
                    stop_events=agent_class_dto.stop_events,
                    hitl_request_events=agent_class_dto.hitl_request_events,
                    hitl_response_events=agent_class_dto.hitl_response_events,
                )
                self.registered_classes.add(agent_class_dto.agent_class)
                logger.info(f"Registered class-level endpoints for agent class: {agent_class_dto.agent_class}")

        # Step 4: Sync agent instances to external provisioners (Langfuse, OpenWebUI)
        await self._sync_agent_instances_to_provisioners()

    async def _broadcast_discovery(self) -> list[AgentClassDTO]:
        """
        Broadcasts a NATS discovery request to all agents and collects responses.
        Updates the last_discovered timestamp for responding agent classes.

        Returns a list of AgentClassDTO for all online agent classes.
        """
        call_id = str(ObjectId())
        discovery_responses: list[AgentClassDiscoveryResponseEvent] = []

        async def discovery_handler(event: AgentClassDiscoveryResponseEvent, topic):
            discovery_responses.append(event)

        nc_publisher = NCPublisher("AgentEndpointsDiscoveryServiceClassDiscoverRequest", self.nc)
        nc_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            self.nc,
            self.topic_manager,
            discovery_handler,
            call_id=call_id,
            subscriber_name="AgentEndpointsDiscoveryServiceClassDiscoveryResponse",
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=self.topic_manager.get_agent_class_discovery_subject_request(call_id=call_id),
        )

        # Wait briefly for responses
        await sleep(10)
        await nc_subscriber.stop()

        unique_agents_dict: dict[str, AgentClassDTO] = {}

        for response in discovery_responses:
            unique_key = response.agent_class

            if unique_key not in unique_agents_dict:
                agent_class_dto = AgentClassDTO.from_discovery_event(response)
                unique_agents_dict[unique_key] = agent_class_dto

                AgentClassEntity.create_or_update(
                    agent_class=agent_class_dto.agent_class,
                    name=agent_class_dto.name,
                    description=agent_class_dto.description,
                    icon=agent_class_dto.icon,
                    form=agent_class_dto.form,
                    agent_config_specs=agent_class_dto.agent_config_specs,
                    is_conversational=agent_class_dto.is_conversational,
                    start_events=agent_class_dto.start_events,
                    stop_events=agent_class_dto.stop_events,
                    hitl_request_events=agent_class_dto.hitl_request_events,
                    hitl_response_events=agent_class_dto.hitl_response_events,
                    network_graph=agent_class_dto.network_graph,
                    templates=[t.model_dump() for t in response.templates],
                )

        return list(unique_agents_dict.values())

    async def _sync_agent_instances_to_provisioners(self) -> None:
        """Sync online agent instances to Langfuse and OpenWebUI workspace models."""
        instances = await AgentService.get_all_agent_instances(t=self.locale_handler, online=True)

        agents_hash = self._compute_agents_hash(instances)
        if await self._agents_hash_unchanged(agents_hash):
            return

        langfuse_ok = await self._sync_agent_instances_to_langfuse(instances)
        openwebui_ok = await self._sync_agent_instances_to_openwebui(instances)
        if langfuse_ok and openwebui_ok:
            await self._store_agents_hash(agents_hash)

    @staticmethod
    def _compute_agents_hash(instances: list[FullAgentInstanceDTO]) -> str:
        keys = sorted(f"{inst.agent_class}/{inst.agent_id}" for inst in instances)
        return hashlib.sha256("\n".join(keys).encode()).hexdigest()

    async def _agents_hash_unchanged(self, new_hash: str) -> bool:
        stored = await self._redis.get(self._AGENTS_HASH_KEY)
        return stored is not None and stored.decode() == new_hash

    async def _store_agents_hash(self, agents_hash: str) -> None:
        await self._redis.set(self._AGENTS_HASH_KEY, agents_hash, ex=self._AGENTS_HASH_TTL)

    async def _sync_agent_instances_to_langfuse(self, instances: list[FullAgentInstanceDTO]) -> bool:
        if self._langfuse_provisioner is None:
            return True
        agent_models = sorted(f"{inst.agent_class}/{inst.agent_id}" for inst in instances)
        try:
            await self._langfuse_provisioner.sync_agents(agent_models)
            return True
        except Exception as e:
            logger.warning("Langfuse agent sync failed (non-fatal): %s", e)
            return False

    async def _sync_agent_instances_to_openwebui(self, instances: list[FullAgentInstanceDTO]) -> bool:
        if self._openwebui_provisioner is None:
            return True
        online_agents = [
            OnlineAgent(
                agent_class=inst.agent_class,
                agent_id=inst.agent_id,
                display_name=inst.name,
            )
            for inst in instances
            if inst.is_conversational
        ]
        try:
            await self._openwebui_provisioner.sync_agents(online_agents)
            return True
        except Exception as e:
            logger.warning("OpenWebUI agent sync failed (non-fatal): %s", e)
            return False

    def _register_class_endpoints(
        self,
        *,
        agent_class: str,
        start_events: list[EventSpecs],
        stop_events: list[EventSpecs],
        hitl_request_events: list[EventSpecs],
        hitl_response_events: list[EventSpecs],
    ):
        """Registers class-level endpoints with dynamic {agent_id} path parameter."""
        base_path = self._get_endpoint_base_path_for_class(agent_class)
        agent_class_snake = snakecase(agent_class)

        stop_event_output_types = [
            ModelCreationService.create_output_model_from_event_specs(stop_event) for stop_event in stop_events
        ]

        hitl_request_output_types = [
            ModelCreationService.create_output_model_from_event_specs(hitl_event) for hitl_event in hitl_request_events
        ]

        # Combine stop events and HITL request events for the response type
        all_output_types = stop_event_output_types + hitl_request_output_types

        if len(all_output_types) == 1:
            response_union_type = all_output_types[0]
        else:
            response_union_type = reduce(or_, all_output_types)

        for start_event_specs in start_events:
            self._register_single_event_endpoints(
                event_specs=start_event_specs,
                base_path=base_path,
                agent_class_snake=agent_class_snake,
                response_union_type=response_union_type,
                agent_class=agent_class,
                expected_type=StartEvent,
                event_type_prefix="send",
            )

        for hitl_response_event_specs in hitl_response_events:
            self._register_single_event_endpoints(
                event_specs=hitl_response_event_specs,
                base_path=base_path,
                agent_class_snake=agent_class_snake,
                response_union_type=response_union_type,
                agent_class=agent_class,
                expected_type=HumanInTheLoopResponseEvent,
                event_type_prefix="send",
            )

    def _register_single_event_endpoints(
        self,
        *,
        event_specs: EventSpecs,
        base_path: str,
        agent_class_snake: str,
        response_union_type: type[BaseModel],
        agent_class: str,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        event_type_prefix: str,
    ):
        """Helper method to register both regular and streaming endpoints for a single event.

        Creates class-level endpoints with {agent_id} as a dynamic path parameter.
        Instance validation occurs at request time.
        """
        event_name = event_specs.event_name
        event_name_snake = snakecase(event_name)
        # Endpoint names no longer include agent_id since it's a path parameter
        endpoint_name = f"{event_type_prefix}_{event_name_snake}_to_{agent_class_snake}"
        path = f"{base_path}/{event_name}"
        stream_endpoint_name = f"stream_{event_name_snake}_to_{agent_class_snake}"
        stream_path = f"{base_path}/{event_name}/stream"

        input_type = ModelCreationService.create_input_model_from_event_specs(event_specs)

        self.app.add_api_route(
            path=path,
            endpoint=self._create_endpoint(
                input_type=input_type,
                response_union_type=response_union_type,
                start_event_parents=event_specs.event_parents,
                start_event_name=event_specs.event_name,
                agent_class=agent_class,
                agent_controller=self.controller,
                expected_type=expected_type,
            ),
            methods=["POST"],
            name=endpoint_name,
            tags=[ApiLocaleString.from_i18n_path("api.controllers.agent.name").en],
            response_model=response_union_type if expected_type == StartEvent else None,
        )

        endpoint_type = "HITL response" if expected_type == HumanInTheLoopResponseEvent else ""
        logger.info(f"Registered {endpoint_type} endpoint: {path}".strip())

        self.app.add_api_route(
            path=stream_path,
            endpoint=self._create_streaming_endpoint(
                input_type=input_type,
                start_event_parents=event_specs.event_parents,
                start_event_name=event_specs.event_name,
                agent_class=agent_class,
                agent_controller=self.controller,
                expected_type=expected_type,
            ),
            methods=["POST"],
            name=stream_endpoint_name,
            tags=[ApiLocaleString.from_i18n_path("api.controllers.agent.name").en],
            response_class=StreamingResponse,
        )
        logger.info(f"Registered {endpoint_type} streaming endpoint: {stream_path}".strip())

    @staticmethod
    def _create_endpoint(
        *,
        input_type: type[BaseModel],
        response_union_type: type[BaseModel],
        start_event_parents: list[str],
        start_event_name: str,
        agent_class: str,
        agent_controller: AgentController,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
    ):
        """Creates a FastAPI endpoint that sends a StartEvent to an agent.

        The agent_id is resolved from the path parameter at request time.
        Instance validation is performed before processing the event.
        """

        async def send_event(
            agent_id: Annotated[str, Path(title="Agent ID", description="The specific agent instance ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            usage_limits: Annotated[UsageLimits, Depends(use_usage_limits)],
            start_event_input: Annotated[input_type, Body],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(agent_controller.user_with_permission(f"aihub.user.agent.{agent_class}.{{agent_id}}")),
            ],
            thread_id: Annotated[str, Query(pattern=r"^[a-f0-9]{24}$")] = None,
            display_id: Annotated[str, Query(pattern=r"^[a-f0-9]{24}$")] = None,
            t: LocaleHandler = Depends(use_locale),
        ) -> response_union_type:
            """Send a specific event type to a specific agent. Returns either a stop event or HITL request event."""
            config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"Agent instance '{agent_class}/{agent_id}' not found")

            await usage_limits.check_and_raise(user, ResourceType.AGENT, agent_class, agent_id, locale=t.locale)

            if thread_id is not None:
                try:
                    thread = await ThreadService.get_thread_by_id(thread_id, t=t)
                except DoesNotExist:
                    ThreadEntity.create_thread(
                        "chat",
                        users=[User(user_id=user.id)],
                        agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
                        thread_id=ObjectId(thread_id),
                    )
                    thread = await ThreadService.get_thread_by_id(thread_id, t=t)

                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise agent_controller.not_authorized_to_view_exception

            response_event = await AgentService.send_agent_input_event(
                nc=nc,
                agent_class=agent_class,
                agent_id=agent_id,
                input_event_parents=start_event_parents,
                input_event_name=start_event_name,
                raw_event_data=start_event_input.model_dump(),
                external_agent_event_distributor=external_agent_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
                user=user,
                t=t,
                expected_type=expected_type,
                subscribe_to_thread=True,
            )

            if isinstance(response_event, ExceptionEvent):
                raise HTTPException(status_code=response_event.http_status_code, detail=response_event.message)

            return response_event

        return send_event

    @staticmethod
    def _create_streaming_endpoint(
        *,
        input_type: type[BaseModel],
        start_event_parents: list[str],
        start_event_name: str,
        agent_class: str,
        agent_controller: AgentController,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
    ):
        """Creates a FastAPI streaming endpoint that sends a StartEvent to an agent and streams all events.

        The agent_id is resolved from the path parameter at request time.
        Instance validation is performed before processing the event.
        """

        async def stream_event(
            agent_id: Annotated[str, Path(title="Agent ID", description="The specific agent instance ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            usage_limits: Annotated[UsageLimits, Depends(use_usage_limits)],
            start_event_input: Annotated[input_type, Body],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(agent_controller.user_with_permission(f"aihub.user.agent.{agent_class}.{{agent_id}}")),
            ],
            thread_id: Annotated[str, Query(pattern=r"^[a-f0-9]{24}$")] = None,
            display_id: Annotated[str, Query(pattern=r"^[a-f0-9]{24}$")] = None,
            t: LocaleHandler = Depends(use_locale),
        ) -> StreamingResponse:
            """Send a specific event type to a specific agent and stream all events as SSE."""
            config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
            if not config:
                raise HTTPException(status_code=404, detail=f"Agent instance '{agent_class}/{agent_id}' not found")

            usage_status = await usage_limits.check_and_raise(
                user, ResourceType.AGENT, agent_class, agent_id, locale=t.locale
            )

            if thread_id is not None:
                try:
                    thread = await ThreadService.get_thread_by_id(thread_id, t=t)
                except DoesNotExist:
                    ThreadEntity.create_thread(
                        "chat",
                        users=[User(user_id=user.id)],
                        agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
                        thread_id=ObjectId(thread_id),
                    )
                    thread = await ThreadService.get_thread_by_id(thread_id, t=t)

                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise agent_controller.not_authorized_to_view_exception

            resources = await AgentService.send_agent_input_event_stream(
                nc=nc,
                agent_class=agent_class,
                agent_id=agent_id,
                input_event_parents=start_event_parents,
                input_event_name=start_event_name,
                raw_event_data=start_event_input.model_dump(),
                external_agent_event_distributor=external_agent_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
                user=user,
                t=t,
                expected_type=expected_type,
                subscribe_to_thread=True,
            )

            async def sse_event_generator():
                """Generator that yields raw events as SSE without conversion"""
                while True:
                    if resources.stop_signal.is_set() and resources.chunk_queue.empty():
                        logger.debug("Stop streaming due to stop_event and empty queue")
                        break
                    try:
                        event = await asyncio.wait_for(resources.chunk_queue.get(), timeout=0.5)

                        # Dump the raw event as JSON for SSE
                        event_data = event.model_dump_json()
                        yield f"data: {event_data}\n\n"

                        resources.chunk_queue.task_done()
                    except TimeoutError:
                        # No new event yet; keep waiting
                        continue
                    except asyncio.CancelledError:
                        break

                # Final event to signal stream end
                yield "data: [DONE]\n\n"

            response_headers = {
                "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Content-Encoding": "identity",
                **UsageLimitMessages.build_usage_warning_headers(usage_status, locale=t.locale),
            }

            return StreamingResponse(
                sse_event_generator(),
                media_type="text/event-stream",
                headers=response_headers,
            )

        return stream_event
