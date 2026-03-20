import abc
import asyncio
import logging

from fastapi import FastAPI
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller

logger = logging.getLogger(__name__)


class EndpointsDiscoveryService(abc.ABC):
    """
    The endpoint discovery service is responsible for periodically discovering the presence of some entity in
    NATs and register dynamic fastapi endpoints accordingly.
    """

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        controller: Controller,
        locale_handler: LocaleHandler,
        discovery_interval: int = 60,
    ):
        self.nc: NATS = nc
        self.app: FastAPI = api_app
        self.controller: Controller = controller
        self.locale_handler: LocaleHandler = locale_handler
        self.discovery_interval: int = discovery_interval
        # For instance-based tracking (used by ProcessEndpointsDiscoveryService)
        self.registered_entities: set[tuple[str, str]] = set()
        # For class-based tracking (used by AgentEndpointsDiscoveryService)
        self.registered_classes: set[str] = set()
        self.running: bool = False
        self.task: asyncio.Task | None = None

    async def start(self) -> bool:
        """Start the discovery loop"""
        if self.running:
            logger.warning("Endpoint discovery service is already running")
            return False

        self.running = True
        self.task = asyncio.create_task(self._discovery_loop())
        logger.info("Endpoint discovery service started")
        return True

    async def stop(self) -> bool:
        """Stop the discovery loop"""
        if not self.running:
            logger.warning("Endpoint discovery service is not running")
            return False

        self.running = False
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task, return_exceptions=True)
        logger.info("Endpoint discovery service stopped")
        return True

    async def _discovery_loop(self):
        """Periodically discover and register endpoints."""
        while self.running:
            try:
                logger.debug("Starting endpoint discovery")
                await self._discover_and_register()
            except Exception as e:
                logger.exception(f"Error in endpoint discovery: {e}")

            await asyncio.sleep(self.discovery_interval)

    @abc.abstractmethod
    async def _discover_and_register(self):
        """Register endpoints for discovered entities."""
        ...

    def _get_endpoint_base_path_for_instance(self, entity_class: str, entity_id: str) -> str:
        """Returns the base path for instance-specific endpoints (used by ProcessEndpointsDiscoveryService)."""
        return f"{self.controller.base_route}/classes/{entity_class}/instances/{entity_id}"

    def _get_endpoint_base_path_for_class(self, entity_class: str) -> str:
        """Returns the base path for class-level endpoints with dynamic {entity_id} path parameter."""
        return f"{self.controller.base_route}/classes/{entity_class}/instances/{{agent_id}}"

    def _deregister_endpoints_for_instance(self, entity_class: str, entity_id: str):
        """Deregister all endpoints for a specific entity instance."""
        base_path = self._get_endpoint_base_path_for_instance(entity_class, entity_id)

        for route in list(self.app.routes):
            if route.path.startswith(f"{base_path}/"):
                self.app.routes.remove(route)
                logger.info(f"Deregistered endpoint: {route.path}")

        self.registered_entities.discard((entity_class, entity_id))

    def _deregister_endpoints_for_class(self, entity_class: str):
        """Deregister all endpoints for an entity class (class-level endpoints with dynamic {agent_id})."""
        base_path = self._get_endpoint_base_path_for_class(entity_class)

        for route in list(self.app.routes):
            if route.path.startswith(f"{base_path}/"):
                self.app.routes.remove(route)
                logger.info(f"Deregistered endpoint: {route.path}")

        self.registered_classes.discard(entity_class)

    # Legacy method names for backward compatibility
    def _get_endpoint_base_path(self, entity_class: str, entity_id: str) -> str:
        """Legacy method - delegates to _get_endpoint_base_path_for_instance."""
        return self._get_endpoint_base_path_for_instance(entity_class, entity_id)

    def _deregister_endpoints(self, entity_class: str, entity_id: str):
        """Legacy method - delegates to _deregister_endpoints_for_instance."""
        self._deregister_endpoints_for_instance(entity_class, entity_id)
