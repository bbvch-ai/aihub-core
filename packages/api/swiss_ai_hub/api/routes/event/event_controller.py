import asyncio
import logging
from datetime import datetime
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Security, WebSocket
from fastapi.params import Path, Query
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence import LLMSpend
from swiss_ai_hub.core.persistence.messaging.entities.persisted_agent_event_entity import (
    PersistedAgentEventEntity,
    TimeRange,
)
from swiss_ai_hub.core.persistence.utils import str_to_object_id
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale, use_locale_ws
from swiss_ai_hub.api.routes.event.dto.event_timeseries import EventTimeseries
from swiss_ai_hub.api.routes.event.dto.thread_reference import ThreadReference
from swiss_ai_hub.api.routes.event.event_service import EventService
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService
from swiss_ai_hub.api.sockets.events.server_to_user.contextualized_agent_event import ContextualizedAgentEvent
from swiss_ai_hub.api.sockets.manager.dependencies.use_ws_manager import use_ws_manager_ws
from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager

logger = logging.getLogger(__name__)

NO_THREAD_ACCESS_DETAIL = "You do not have access to this thread. Please contact the process owner."


def _acting_tenant_id(user: UserIdentity) -> str | None:
    """The tenant a non-sysadmin caller is scoped to; None only when they act outside any tenant."""
    return user.acting_within_tenant.id if user.acting_within_tenant else None


class EventController(TenantScopedController):
    """
    A controller that manages the event-related endpoints, including:
    - Retrieving a user’s persisted events.
    - Establishing a WebSocket connection for real-time two-way messaging.
    The `EventController` provides HTTP and WebSocket endpoints to handle these use cases.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.event.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.event.description")
    icon = "mage:broadcast"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/events", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_agent_events_in_thread(self, path: str = "/agents/threads/{thread_id}") -> Self:
        @self.router.get(path, tags=self.tags)
        async def get_agent_events_in_thread(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            thread_id: Annotated[str, Path(title="Thread ID", pattern=r"^[a-f0-9]{24}$")],
            display_id: Annotated[str, Query(pattern=r"^[a-f0-9]{24}$")] = None,
        ) -> list[ContextualizedAgentEvent]:
            """
            Returns all events in a given thread
            """
            if display_id is not None and thread_id is None:
                raise HTTPException(
                    status_code=400, detail="If display_id is provided, thread_id must also be provided."
                )

            thread = await ThreadService.get_thread_by_id(thread_id=thread_id, t=t)
            user_in_thread = user.id in [u.id for u in thread.users]
            thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                thread.process_class, thread.process_id
            )
            if not (user_in_thread or thread_belongs_to_users_process):
                raise HTTPException(
                    status_code=403,
                    detail=NO_THREAD_ACCESS_DETAIL,
                )

            # Offloaded: reads and deserialises every display event in the thread, so its cost grows
            # with conversation length. On the event loop that stalls every concurrent request.
            return await asyncio.to_thread(
                EventService.get_events_in_thread,
                locale=t.locale,
                thread_id=str_to_object_id(thread_id),
                display_id=str_to_object_id(display_id) if display_id else None,
            )

        return self

    def resolve_thread_for_display(self, path: str = "/agents/displays/{display_id}/thread") -> Self:
        @self.router.get(path, tags=self.tags)
        async def resolve_thread_for_display(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            display_id: Annotated[str, Path(title="Display ID", pattern=r"^[a-f0-9]{24}$")],
        ) -> ThreadReference:
            """
            Resolves the thread that owns a display so the chat-UI side panel can open the correct per-agent thread
            without recomputing the salted thread_id.
            """
            thread_id = EventService.thread_id_for_display(display_id=display_id)
            if thread_id is None:
                raise HTTPException(status_code=404, detail="No thread found for the given display.")

            thread = await ThreadService.get_thread_by_id(thread_id=thread_id, t=t)
            user_in_thread = user.id in [u.id for u in thread.users]
            thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                thread.process_class, thread.process_id
            )
            if not (user_in_thread or thread_belongs_to_users_process):
                raise HTTPException(
                    status_code=403,
                    detail=NO_THREAD_ACCESS_DETAIL,
                )

            return ThreadReference(thread_id=thread_id)

        return self

    def get_agent_event_timeseries(self, route: str = "/agents/timeseries/{time_range}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_agent_event_timeseries(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
            time_range: Annotated[
                TimeRange,
                Path(
                    title="Time Range",
                    description="Time range for the statistics (1h, 24h, 30d, 365d)",
                ),
            ],
            thread_id: Annotated[str, Query()] = None,
            agent_class: Annotated[str, Query(title="Agent Class")] = None,
            agent_id: Annotated[str, Query(title="Agent ID")] = None,
            event_name: Annotated[str, Query(title="Event Name")] = None,
        ) -> EventTimeseries:
            """
            Retrieves time-based statistics.
            Returns event counts in time buckets with resolution based on the time range:
            - 1h: 1 minute resolution
            - 24h: 1 hour resolution
            - 30d: 1 day resolution
            - 365d: 1 week resolution
            """
            access_checker = AccessChecker.from_user(user)

            if agent_id and not agent_class:
                raise HTTPException(
                    status_code=400, detail="If agent_id is provided, agent_class must also be provided."
                )

            if agent_class and agent_id:
                if not access_checker.has_access_to_agent(agent_class, agent_id):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User {user.id} does not have access to agent {agent_class}:{agent_id}",
                    )

            if agent_class:
                if not access_checker.has_access_to_agent_class(agent_class):
                    raise HTTPException(
                        status_code=403,
                        detail=f"User {user.id} does not have access to agent class {agent_class}",
                    )

            if thread_id:
                thread = await ThreadService.get_thread_by_id(thread_id=thread_id, t=t)
                user_in_thread = user.id in [u.id for u in thread.users]
                thread_belongs_to_users_process = AccessChecker.from_user(user).has_access_to_process(
                    thread.process_class, thread.process_id
                )
                if not (user_in_thread or thread_belongs_to_users_process):
                    raise HTTPException(
                        status_code=403,
                        detail=NO_THREAD_ACCESS_DETAIL,
                    )

            # Offloaded: an unfiltered range aggregates the whole agent_events collection, which took
            # minutes in production and, on the event loop, pushed concurrent token validation past
            # its Keycloak timeout — failing valid logins with 500s (aihub-core-private#186).
            return await asyncio.to_thread(
                EventService.get_event_timeseries,
                time_range,
                agent_id=agent_id,
                agent_class=agent_class,
                event_name=event_name,
                thread_id=thread_id,
            )

        return self

    def ws(self, path: str = "/ws") -> Self:
        @self.router.websocket(path)
        async def websocket_endpoint(
            websocket: WebSocket,
            ws_manager: Annotated[WebSocketManager, Depends(use_ws_manager_ws)],
            t: Annotated[LocaleHandler, Depends(use_locale_ws)],
        ):
            """
            Establishes a WebSocket connection. The first message must contain a token for authentication.
            If the token is valid, the user can receive live event streams.
            Note that this websocket connection does NOT accept events from the user due to security
            reasons. Please use the dedicated agent or process endpoints to publish events.
            """
            await websocket.accept()

            first_message = await websocket.receive_json()
            token = first_message.get("token")

            if token.startswith("Bearer "):
                token = token[7:]

            if not token:
                await websocket.close(code=4000, reason="No token provided")
                return

            try:
                user = await self.auth.authenticate_token(token)
            except HTTPException as e:
                logger.exception(e)
                await websocket.close(code=4001, reason=f"Invalid token: {e.detail}")
                return
            except Exception as e:
                logger.exception(e)
                await websocket.close(code=4002, reason="Token validation error")
                return

            await EventService.event_websocket_connection(
                websocket,
                ws_manager,
                user,
                t,
            )

        return self

    def get_llm_spend_by_user(self, route: str = "/spend/users") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_llm_spend_by_user(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.?>"))],
            since: Annotated[
                datetime | None,
                Query(
                    description="Only count calls at or after this time. "
                    f"Defaults to the last {PersistedAgentEventEntity.SPEND_WINDOW_DAYS} days."
                ),
            ] = None,
        ) -> list[LLMSpend]:
            """
            LLM spend per user, from the platform's own cost events.

            Scoped to the caller's acting tenant: spend reveals who used which agents and how much,
            so a tenant admin must not see other tenants' users. Only a sysadmin, who acts outside
            any single tenant, sees the whole platform.
            """
            if user.is_sys_admin:
                return await EventService.get_llm_spend_by_user(since=since)

            # Deny rather than fall open: an unset acting tenant would otherwise mean "no filter",
            # handing a single-tenant admin every tenant's user spend.
            tenant_id = _acting_tenant_id(user)
            if tenant_id is None:
                raise HTTPException(status_code=403, detail="Must act within a tenant to view user spend.")
            return await EventService.get_llm_spend_by_user(tenant_id=tenant_id, since=since)

        return self

    def get_llm_spend_by_tenant(self, route: str = "/spend/tenants") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_llm_spend_by_tenant(
            user: Annotated[UserIdentity, Security(self.sys_admin_user())],
            since: Annotated[
                datetime | None,
                Query(
                    description="Only count calls at or after this time. "
                    f"Defaults to the last {PersistedAgentEventEntity.SPEND_WINDOW_DAYS} days."
                ),
            ] = None,
        ) -> list[LLMSpend]:
            """
            LLM spend per tenant across the whole platform.

            Sysadmin-only: a cross-tenant total is exactly the view a single tenant must not have.
            """
            del user
            return await EventService.get_llm_spend_by_tenant(since=since)

        return self
