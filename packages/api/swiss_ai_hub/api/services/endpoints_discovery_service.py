import abc
import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import ClassVar

from fastapi import FastAPI
from fastapi.routing import APIRoute
from nats.aio.client import Client as NATS
from pydantic import BaseModel
from redis.asyncio import Redis
from swiss_ai_hub.core.discovery import DiscoveryKind, DiscoverySettings
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence import DiscoveryRoundEntity
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.services.discovery_recorder_lease import DiscoveryRecorderLease

logger = logging.getLogger(__name__)


class EndpointsDiscoveryService[TClassDTO: BaseModel](abc.ABC):
    """
    The endpoint discovery service is responsible for periodically discovering the presence of some entity in
    NATs and register dynamic fastapi endpoints accordingly.

    A class is online while it has answered one of the last `MISSED_ROUNDS_BEFORE_OFFLINE` *completed* rounds.
    Only a round that stayed connected to NATS from broadcast to the end of the wait and finished within its
    timeout is recorded, so a broken round — the event loop starved, NATS reconnecting — changes no class's
    status instead of taking every class offline at once. Every API process runs rounds for its own
    endpoints, but only the holder of the `DiscoveryRecorderLease` records them.
    """

    discovery_kind: ClassVar[DiscoveryKind]

    def __init__(
        self,
        nc: NATS,
        api_app: FastAPI,
        controller: Controller,
        locale_handler: LocaleHandler,
        redis: Redis,
        settings: DiscoverySettings | None = None,
    ):
        self.nc: NATS = nc
        self.app: FastAPI = api_app
        self.controller: Controller = controller
        self.locale_handler: LocaleHandler = locale_handler
        self.settings: DiscoverySettings = settings or DiscoverySettings()
        self._recorder_lease = DiscoveryRecorderLease(redis, self.discovery_kind, self.settings)
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
        await self._recorder_lease.release()
        logger.info("Endpoint discovery service stopped")
        return True

    async def _discovery_loop(self) -> None:
        """Periodically discover and register endpoints."""
        while self.running:
            if await self._run_round():
                await self._run_after_round()
            await asyncio.sleep(self.settings.INTERVAL_SECONDS)

    async def _run_round(self) -> bool:
        """Runs one round under its timeout; a round that fails in any way is logged and reported incomplete."""
        logger.debug(f"Starting {self.discovery_kind} discovery round")
        try:
            async with asyncio.timeout(self.settings.ROUND_TIMEOUT_SECONDS):
                return await self._discover_and_register()
        except TimeoutError:
            logger.error(
                f"{self.discovery_kind.capitalize()} discovery round stalled for more than "
                f"{self.settings.ROUND_TIMEOUT_SECONDS}s and was abandoned; no class status changed."
            )
        except Exception as e:
            logger.exception(f"{self.discovery_kind.capitalize()} discovery round failed; no class status changed: {e}")
        return False

    async def _run_after_round(self) -> None:
        """Outside the round's timeout, so a slow downstream sync is not mistaken for a stalled round."""
        try:
            await self._after_round()
        except Exception as e:
            logger.exception(f"Work after the {self.discovery_kind} discovery round failed: {e}")

    async def _discover_and_register(self) -> bool:
        """Broadcasts one round, records it if it completed, and reconciles the dynamic endpoints."""
        started_at = datetime.now()
        if not self._nats_connected("before broadcasting"):
            return False
        reconnects_before = self.nc.stats["reconnects"]

        discovered = await self._broadcast_discovery()

        # nats-py does not raise while it reconnects: the request is buffered and answers are lost. Counting
        # that round would mark every class as having missed it, even when the connection is back by now.
        if not self._nats_connected("while collecting answers") or self._nats_reconnected_since(reconnects_before):
            return False

        if await self._recorder_lease.held():
            await DiscoveryRoundEntity.record_completed(self.discovery_kind, started_at, self.settings)
        discovered_names = {self._class_name_of(dto) for dto in discovered}
        online_class_names = await self._online_class_names() | discovered_names

        for entity_class in list(self.registered_classes):
            if entity_class not in online_class_names:
                self._deregister_endpoints_for_class(entity_class)

        self.app.openapi_schema = None

        for dto in discovered:
            entity_class = self._class_name_of(dto)
            if entity_class not in self.registered_classes:
                self._register_discovered_class(dto)
                self.registered_classes.add(entity_class)
                logger.info(f"Registered class-level endpoints for {self.discovery_kind} class: {entity_class}")
        return True

    def _nats_connected(self, moment: str) -> bool:
        if self.nc.is_connected:
            return True
        logger.error(
            f"NATS was not connected {moment} in the {self.discovery_kind} discovery round; "
            "the round is not counted and no class status changed."
        )
        return False

    def _nats_reconnected_since(self, reconnects_before: int) -> bool:
        if self.nc.stats["reconnects"] == reconnects_before:
            return False
        logger.error(
            f"NATS reconnected while the {self.discovery_kind} discovery round collected answers; "
            "the round is not counted and no class status changed."
        )
        return True

    async def _stamp_answer(self, class_name: str, stamp: Callable[[], Awaitable[object]]) -> bool:
        """Saves one class's answer; a class whose answer cannot be saved has not answered.

        Isolated so that one class whose answer the database rejects cannot fail every round, which would
        freeze every other class's status until `MAX_SILENCE_SECONDS` takes them all offline. A synchronous
        write must reach here already offloaded to a thread: this process also serves every request, and a
        blocking write per class could push the round past its timeout.
        """
        try:
            await stamp()
        except Exception as e:
            logger.exception(
                f"Could not save the {self.discovery_kind} discovery answer of {class_name}; "
                f"it counts as not having answered this round: {e}"
            )
            return False
        return True

    @abc.abstractmethod
    async def _broadcast_discovery(self) -> list[TClassDTO]:
        """Broadcasts the discovery request, waits for answers and stamps `last_discovered` for each class."""
        ...

    @abc.abstractmethod
    def _class_name_of(self, dto: TClassDTO) -> str: ...

    @abc.abstractmethod
    def _register_discovered_class(self, dto: TClassDTO) -> None: ...

    @abc.abstractmethod
    async def _online_class_names(self) -> set[str]:
        """Classes online under the completed-rounds rule."""
        ...

    async def _after_round(self) -> None:
        """Work that needs the round's outcome but must not count against its timeout."""

    @property
    def _route_prefix(self) -> str:
        """The URL prefix for this controller, including ``/{tenant_id}`` for tenant-scoped controllers."""
        from swiss_ai_hub.core.routes.tenant_scoped_controller import TenantScopedController

        if isinstance(self.controller, TenantScopedController):
            return f"/{{tenant_id}}{self.controller.base_route}"
        return self.controller.base_route

    def _get_endpoint_base_path_for_instance(self, entity_class: str, entity_id: str) -> str:
        """Returns the base path for instance-specific endpoints (used by ProcessEndpointsDiscoveryService)."""
        return f"{self._route_prefix}/classes/{entity_class}/instances/{entity_id}"

    def _get_endpoint_base_path_for_class(self, entity_class: str) -> str:
        """Returns the base path for class-level endpoints with dynamic {entity_id} path parameter."""
        return f"{self._route_prefix}/classes/{entity_class}/instances/{{agent_id}}"

    def _deregister_endpoints_for_instance(self, entity_class: str, entity_id: str):
        """Deregister all endpoints for a specific entity instance."""
        self._deregister_routes_under(self._get_endpoint_base_path_for_instance(entity_class, entity_id))
        self.registered_entities.discard((entity_class, entity_id))

    def _deregister_endpoints_for_class(self, entity_class: str):
        """Deregister all endpoints for an entity class (class-level endpoints with dynamic {agent_id})."""
        self._deregister_routes_under(self._get_endpoint_base_path_for_class(entity_class))
        self.registered_classes.discard(entity_class)

    def _deregister_routes_under(self, base_path: str) -> None:
        """Remove the dynamic endpoints below `base_path`.

        Only `APIRoute`s are candidates: since FastAPI 0.14x every controller mounted through `include_router` sits in
        `app.routes` as an `_IncludedRouter` wrapper without a `path`, and the dynamic endpoints are added with
        `add_api_route`, so they are top-level `APIRoute`s.
        """
        for route in list(self.app.routes):
            if isinstance(route, APIRoute) and route.path.startswith(f"{base_path}/"):
                self.app.routes.remove(route)
                logger.info(f"Deregistered endpoint: {route.path}")

        self.app.openapi_schema = None

    # Legacy method names for backward compatibility
    def _get_endpoint_base_path(self, entity_class: str, entity_id: str) -> str:
        """Legacy method - delegates to _get_endpoint_base_path_for_instance."""
        return self._get_endpoint_base_path_for_instance(entity_class, entity_id)

    def _deregister_endpoints(self, entity_class: str, entity_id: str):
        """Legacy method - delegates to _deregister_endpoints_for_instance."""
        self._deregister_endpoints_for_instance(entity_class, entity_id)
