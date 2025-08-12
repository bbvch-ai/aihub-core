import asyncio
import logging
from functools import reduce
from operator import or_
from typing import Annotated, override

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_agent_event_distributor import (
    use_external_agent_event_distributor,
)
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import ExceptionEvent, InstanceDiscoveryRequestEvent, StopEvent
from aihub_lib.nats.events.discovery.agent.AgentInstanceDiscoveryResponseEvent import (
    AgentInstanceDiscoveryResponseEvent,
)
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics import AgentInstanceDiscoveryTopic
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Security
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from stringcase import snakecase

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO
from aihub_api.routes.thread.ThreadService import ThreadService
from aihub_api.services.EndpointsDiscoveryService import EndpointsDiscoveryService
from aihub_api.services.ModelCreationService import ModelCreationService

logger = logging.getLogger(__name__)


class AgentEndpointsDiscoveryService(EndpointsDiscoveryService):
    """
    This service ensures that new agents in the system are automatically registered.
    This ensures that the API and the Agents are decoupled.
    """

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        controller: AgentController,
        locale_handler: LocaleHandler,
        discovery_interval: int = 60,
    ):
        super().__init__(nc, api_app, controller, locale_handler, discovery_interval)
        self.controller: AgentController = controller
        self.topic_manager: AgentTopicManager = AgentTopicManager()

        self.nc_publisher: NCPublisher[AgentInstanceDiscoveryResponseEvent] | None = None
        self.discovery_event_subscriber: NCSubscriber[InstanceDiscoveryRequestEvent] | None = None

    async def _discovery_handler(self, event: InstanceDiscoveryRequestEvent, topic: AgentInstanceDiscoveryTopic):
        """
        Responds to discovery requests by publishing an AgentDiscoveryResponseEvent that includes the basic
        agent configuration as well as some carefully crafted event specifications.
        """
        logger.debug(f"Received discovery request for {topic.agent_class} with id {topic.agent_id}.")

        subject = self.topic_manager.get_agent_instance_discovery_subject_response(
            topic.call_id, topic.agent_class, topic.agent_id
        )

        agent_instances: list[AgentInstanceDTO] = []
        if topic.agent_class == "*":
            agent_instances = await AgentService.discover_agent_instances(self.nc)

            if topic.agent_id != "*":
                agent_instances = [agent for agent in agent_instances if agent.agent_id == topic.agent_id]

        elif topic.agent_id == "*":
            agent_instances = await AgentService.discover_agent_instances_by_class(
                nc=self.nc, agent_class=topic.agent_class
            )

        else:
            agent_instances.append(
                await AgentService.discover_agent_instance(self.nc, topic.agent_class, topic.agent_id)
            )

        for agent_instance in agent_instances:
            agent_discovery_response_event = agent_instance.to_discovery_response_event()
            await self.nc_publisher.publish_event(agent_discovery_response_event, subject)

    @override
    async def start(self):
        started = await super().start()
        if not started:
            logger.debug("Agent discovery service already running")
            return

        self.discovery_event_subscriber = AgentNCSubscriber.for_agent_instance_discovery_request_events(
            nc=self.nc,
            topic_manager=AgentTopicManager(),
            handler=self._discovery_handler,
        )
        await self.discovery_event_subscriber.start()
        logger.info("Agent discovery service started")

    @override
    async def stop(self):
        stopped = await super().stop()
        if not stopped:
            logger.debug("Agent discovery service already stopped")
            return

        await self.discovery_event_subscriber.stop()
        logger.info("Agent discovery service stopped")

    @override
    async def _discover_and_register(self):
        """Discovers agents and registers endpoints that accept their starting events"""
        agents: list[AgentInstanceDTO] = await AgentService.discover_agent_instances(self.nc)

        # Deregister old endpoints
        for registered_agent_class, registered_agent_id in list(self.registered_entities):
            self._deregister_endpoints(registered_agent_class, registered_agent_id)
        self.app.openapi_schema = None

        # Register new endpoints for configured agents
        for agent in agents:
            agent_key = (agent.agent_class, agent.agent_id)

            self._register_agent_endpoints(
                agent_class=agent.agent_class,
                agent_id=agent.agent_id,
                start_events=agent.start_events,
                stop_events=agent.stop_events,
                config=agent.agent_config,
            )

            self.registered_entities.add(agent_key)
            logger.info(f"Registered endpoints for configured agent: {agent.agent_class}.{agent.agent_id}")

    def _register_agent_endpoints(
        self,
        agent_class: str,
        agent_id: str,
        start_events: list[EventSpecs],
        stop_events: list[EventSpecs],
        config: AgentConfig,
    ):
        """Registers endpoints for sending events to an agent"""
        base_path = self._get_endpoint_base_path(agent_class, agent_id)
        agent_class_snake = snakecase(agent_class)
        agent_id_snake = snakecase(agent_id)

        stop_event_output_types = [
            ModelCreationService.create_output_model_from_event_specs(stop_event) for stop_event in stop_events
        ]

        if len(stop_event_output_types) == 1:
            stop_event_union_type = stop_event_output_types[0]
        else:
            stop_event_union_type = reduce(or_, stop_event_output_types)

        for start_event_specs in start_events:
            start_event_name = snakecase(start_event_specs.event_name)
            endpoint_name = f"send_{start_event_name}_to_{agent_class_snake}_{agent_id_snake}"
            path = f"{base_path}/{start_event_name}"
            stream_endpoint_name = f"stream_{start_event_name}_to_{agent_class_snake}_{agent_id_snake}"
            stream_path = f"{base_path}/{start_event_name}/stream"

            start_event_input_type = ModelCreationService.create_input_model_from_event_specs(start_event_specs)

            # Register regular endpoint (existing)
            self.app.add_api_route(
                path=path,
                endpoint=self._create_endpoint(
                    input_type=start_event_input_type,
                    stop_event_union_type=stop_event_union_type,
                    start_event_parents=start_event_specs.event_parents,
                    start_event_name=start_event_specs.event_name,
                    agent_class=agent_class,
                    agent_id=agent_id,
                    agent_controller=self.controller,
                    agent_config=config,
                ),
                methods=["POST"],
                name=endpoint_name,
                tags=["Agents"],
                response_model=stop_event_union_type,
            )
            logger.info(f"Registered endpoint: {path}")

            # Register streaming endpoint (new)
            self.app.add_api_route(
                path=stream_path,
                endpoint=self._create_streaming_endpoint(
                    input_type=start_event_input_type,
                    start_event_parents=start_event_specs.event_parents,
                    start_event_name=start_event_specs.event_name,
                    agent_class=agent_class,
                    agent_id=agent_id,
                    agent_controller=self.controller,
                    agent_config=config,
                ),
                methods=["POST"],
                name=stream_endpoint_name,
                tags=["Agents"],
                response_class=StreamingResponse,
            )
            logger.info(f"Registered streaming endpoint: {stream_path}")

    @staticmethod
    def _create_endpoint(
        input_type: type[BaseModel],
        stop_event_union_type: type[BaseModel],
        start_event_parents: list[str],
        start_event_name: str,
        agent_class: str,
        agent_id: str,
        agent_controller: AgentController,
        agent_config: AgentConfig,
    ):
        """Creates a FastAPI endpoint that sends a StartEvent to an agent"""

        async def send_event(
            nc: Annotated[NATS, Depends(use_nats)],
            start_event_input: Annotated[input_type, Body],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(agent_controller.user_with_permission(f"aihub.user.agent.{agent_class}.{agent_id}")),
            ],
            thread_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            display_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            t: LocaleHandler = Depends(use_locale),
        ) -> stop_event_union_type:
            """Send a specific event type to a specific agent. Returns any possible stop event type."""
            if thread_id is not None:
                thread = await ThreadService.get_thread_by_id(thread_id, t=t)

                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise agent_controller.not_authorized_to_view_exception

            response_event: StopEvent | ExceptionEvent = await AgentService.send_agent_start_event(
                nc=nc,
                agent_class=agent_class,
                agent_id=agent_id,
                start_event_parents=start_event_parents,
                start_event_name=start_event_name,
                raw_event_data=start_event_input.model_dump(),
                external_agent_event_distributor=external_agent_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
                user=user,
                t=t,
                agent_config=agent_config,
            )

            if isinstance(response_event, ExceptionEvent):
                raise HTTPException(status_code=response_event.http_status_code, detail=response_event.message)

            return response_event

        return send_event

    @staticmethod
    def _create_streaming_endpoint(
        input_type: type[BaseModel],
        start_event_parents: list[str],
        start_event_name: str,
        agent_class: str,
        agent_id: str,
        agent_controller: AgentController,
        agent_config: AgentConfig,
    ):
        """Creates a FastAPI streaming endpoint that sends a StartEvent to an agent and streams all events"""

        async def stream_event(
            nc: Annotated[NATS, Depends(use_nats)],
            start_event_input: Annotated[input_type, Body],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            user: Annotated[
                UserIdentity,
                Security(agent_controller.user_with_permission(f"aihub.user.agent.{agent_class}.{agent_id}")),
            ],
            thread_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            display_id: Annotated[str, Query(pattern="/^[a-f\d]{24}$/i")] = None,
            t: LocaleHandler = Depends(use_locale),
        ) -> StreamingResponse:
            """Send a specific event type to a specific agent and stream all events as SSE."""
            if thread_id is not None:
                thread = await ThreadService.get_thread_by_id(thread_id, t=t)

                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise agent_controller.not_authorized_to_view_exception

            resources = await AgentService.send_agent_start_event_stream(
                nc=nc,
                agent_class=agent_class,
                agent_id=agent_id,
                start_event_parents=start_event_parents,
                start_event_name=start_event_name,
                raw_event_data=start_event_input.model_dump(),
                external_agent_event_distributor=external_agent_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
                user=user,
                t=t,
                agent_config=agent_config,
            )

            async def sse_event_generator():
                """Generator that yields raw events as SSE without conversion"""
                while True:
                    if resources.stop_signal.is_set() and resources.chunk_queue.empty():
                        logger.debug("Stop streaming due to stop_event and empty queue")
                        break
                    try:
                        # Get the next event from the queue
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

            return StreamingResponse(
                sse_event_generator(),
                media_type="text/event-stream",
            )

        return stream_event
