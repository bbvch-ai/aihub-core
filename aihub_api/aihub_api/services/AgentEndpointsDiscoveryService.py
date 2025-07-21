import logging
import time
from functools import reduce
from operator import or_
from typing import Annotated, Any

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_agent_event_distributor import (
    use_external_agent_event_distributor,
)
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import BaseEvent, ExceptionEvent, InstanceDiscoveryRequestEvent
from aihub_lib.nats.events.discovery.agent.AgentInstanceDiscoveryResponseEvent import (
    AgentInstanceDiscoveryResponseEvent,
)
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics import AgentInstanceDiscoveryTopic
from bson import ObjectId
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Security
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from stringcase import snakecase
from typing_extensions import override

from aihub_api.agents.AgentInstance import AgentInstance
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.agent.AgentService import AgentService
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

    async def discovery_handler(self, event: InstanceDiscoveryRequestEvent, topic: AgentInstanceDiscoveryTopic):
        """
        Responds to discovery requests by publishing an AgentDiscoveryResponseEvent that includes the basic
        agent configuration as well as some carefully crafted event specifications.
        """
        logger.debug(f"Received discovery request for {topic.agent_class} with id {topic.agent_id}.")

        subject = self.topic_manager.get_agent_instance_discovery_subject_response(
            topic.call_id, topic.agent_class, topic.agent_id
        )

        agents: list[AgentInstance] = []
        if topic.agent_class == "*":
            agents = await AgentService.discover_agent_instances(self.nc)

            if topic.agent_id != "*":
                agents = [agent for agent in agents if agent.agent_id == topic.agent_id]

        elif topic.agent_id == "*":
            agents = await AgentService.discover_agent_instances_by_class(nc=self.nc, agent_class=topic.agent_class)

        else:
            agents.append(await AgentService.discover_agent_instance(self.nc, topic.agent_class, topic.agent_id))

        for agent in agents:
            agent_discovery_response_event = AgentInstanceDiscoveryResponseEvent.from_agent_instance(agent)
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
            handler=self.discovery_handler,
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
        agents: list[AgentInstance] = await AgentService.discover_agent_instances(self.nc)

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

            start_event_input_type = ModelCreationService.create_input_model_from_event_specs(start_event_specs)

            self.app.add_api_route(
                path=path,
                endpoint=self.create_endpoint(
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

    @staticmethod
    def create_endpoint(
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
            """
            Send a specific event type to a specific agent. Returns any possible stop event type.
            """
            if thread_id is not None:
                thread = await ThreadService.get_thread_by_id(thread_id, t=t)

                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise agent_controller.not_authorized_to_view_exception

            json_data: dict[str, Any] = {
                "event_id": str(ObjectId()),
                "created_at": time.time_ns(),
                "user": user,
                **start_event_input.model_dump(),
                "locale": t.locale,
                "_parent_event_names": start_event_parents,
                "_event_name": start_event_name,
                "agent_config": agent_config.model_dump(),
            }
            event: BaseEvent = BaseEvent.deserialize_event(json_data)

            stop_event = await AgentService.send_event(
                nc,
                external_agent_event_distributor,
                user,
                event,
                agent_class,
                agent_id,
                thread_id,
                display_id,
            )

            if isinstance(stop_event, ExceptionEvent):
                raise HTTPException(status_code=stop_event.http_status_code, detail=stop_event.message)

            return stop_event

        return send_event
