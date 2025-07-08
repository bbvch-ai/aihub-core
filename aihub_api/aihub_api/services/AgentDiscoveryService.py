import asyncio
import logging
import time
from typing import Annotated, Any, Dict, List, Set, Tuple, Type, Union

from aihub_api.routes.agent.AgentController import AgentController
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import BaseEvent, ExceptionEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from bson import ObjectId
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Security
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from stringcase import snakecase

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO

logger = logging.getLogger(__name__)


class AgentDiscoveryService:
    """
    This service ensures that new agents in the system are automatically registered.
    This ensures that the API and the Agents are decoupled.
    """

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        agent_controller: AgentController,
        locale_handler: LocaleHandler,
        discovery_interval: int = 60,
    ):
        self.nc = nc
        self.app = api_app
        self.agent_controller = agent_controller
        self.locale_handler = locale_handler
        self.discovery_interval = discovery_interval
        self.registered_agents: Set[Tuple[str, str]] = set()
        self.running = False
        self.task = None

    async def start(self):
        if self.running:
            return

        self.running = True
        self.task = asyncio.create_task(self._discovery_loop())
        logger.info("Agent discovery service started")

    async def stop(self):
        if not self.running:
            return

        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("Agent discovery service stopped")

    async def _discovery_loop(self):
        while self.running:
            try:
                logger.debug("Starting agent discovery")
                await self._discover_and_register_agents()
            except Exception as e:
                logger.error(f"Error in agent discovery: {e}")

            await asyncio.sleep(self.discovery_interval)

    async def _discover_and_register_agents(self):
        agents: List[AgentDTO] = await AgentService.discover_agents(self.nc, self.locale_handler)

        for agent in agents:
            agent_key = (agent.agent_class, agent.agent_id)

            if agent_key in self.registered_agents:
                continue

            self._register_agent_endpoints(agent.agent_class, agent.agent_id, agent.start_events, agent.stop_events)

            self.registered_agents.add(agent_key)
            logger.info(f"Registered endpoints for agent: {agent.agent_class}.{agent.agent_id}")

    def _register_agent_endpoints(
        self, agent_class: str, agent_id: str, start_events: List[EventSpecs], stop_events: List[EventSpecs]
    ):
        agent_class_name = snakecase(agent_class)
        agent_id_snake = snakecase(agent_id)

        stop_event_output_types = [
            EventModelCreationService.create_output_model_from_specs(stop_event) for stop_event in stop_events
        ]

        if len(stop_event_output_types) == 1:
            stop_event_union_type = stop_event_output_types[0]
        else:
            stop_event_union_type = Union[tuple(stop_event_output_types)]

        for start_event_specs in start_events:
            start_event_name = snakecase(start_event_specs.event_name)

            endpoint_name = f"send_{start_event_name}_to_{agent_class_name}_{agent_id_snake}"
            endpoint_route = f"/{agent_class_name}/{agent_id_snake}/{start_event_name}"
            path = f"/agents{endpoint_route}"

            start_event_input_type = EventModelCreationService.create_input_model_from_specs(start_event_specs)

            self.app.add_api_route(
                path=path,
                endpoint=self.create_endpoint(
                    input_type=start_event_input_type,
                    stop_event_union_type=stop_event_union_type,
                    start_event_parents=start_event_specs.event_parents,
                    agent_class=agent_class,
                    agent_id=agent_id,
                    agent_controller=self.agent_controller,
                ),
                methods=["POST"],
                name=endpoint_name,
                tags=["Agents"],
                response_model=stop_event_union_type,
            )
            logger.info(f"Registered endpoint: {path}")

    @staticmethod
    def create_endpoint(
        input_type: Type[BaseModel],
        stop_event_union_type: Type[BaseEvent],
        start_event_parents: List[str],
        agent_class: str,
        agent_id: str,
        agent_controller: AgentController,
    ):

        async def send_event(
            nc: Annotated[NATS, Depends(use_nats)],
            start_event_input: Annotated[input_type, Body],
            external_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_event_distributor)
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

            json_data: Dict[str, Any] = {
                "event_id": str(ObjectId()),
                "created_at": time.time_ns(),
                "user": user.model_dump(),
                **start_event_input.model_dump(),
                "locale": t.locale,
                "_parent_event_names": start_event_parents,
            }
            event: BaseEvent = BaseEvent.deserialize_event(json_data)

            stop_event = await AgentService.send_event(
                nc,
                external_event_distributor,
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
