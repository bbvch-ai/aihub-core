import asyncio
import logging
from typing import List, Set, Tuple, Union, Type

from openai import BaseModel

from aihub_api.events.EventModelCreationService import EventModelCreationService
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import EventSpecs
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.AgentController import AgentController
from aihub_api.routes.agent.AgentService import AgentService

logger = logging.getLogger(__name__)


class AgentDiscoveryService:
    """
    This service ensures that new agents in the system are automatically registered.
    This ensures that the API and the Agents are decoupled.
    """

    def __init__(
        self, nc: NATS, agent_controller: AgentController, locale_handler: LocaleHandler, discovery_interval: int = 60
    ):
        self.nc = nc
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
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Agent discovery service stopped")

    async def _discovery_loop(self):
        while self.running:
            try:
                await self._discover_and_register_agents()
            except Exception as e:
                logger.error(f"Error in agent discovery: {e}")

            await asyncio.sleep(self.discovery_interval)

    async def _discover_and_register_agents(self):
        agents = await AgentService.discover_agents(self.nc, self.locale_handler)

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
        # Create an endpoint for this event type
        self.agent_controller.send_event_to(
            agent_class=agent_class,
            agent_id=agent_id,
            start_events=start_events,
            stop_events=stop_events,
        )
