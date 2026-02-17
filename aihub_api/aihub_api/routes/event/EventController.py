import logging
from typing import Annotated, Self

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.messaging.entities.PersistedAgentEventEntity import TimeRange
from aihub_lib.persistence.utils import str_to_object_id
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Security, WebSocket
from fastapi.params import Path, Query

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.i18n.dependencies.use_locale import use_locale, use_locale_ws
from aihub_api.routes.event.dto.EventTimeseries import EventTimeseries
from aihub_api.routes.event.EventService import EventService
from aihub_api.routes.thread.ThreadService import ThreadService
from aihub_api.sockets.events.server_to_user.ContextualizedAgentEvent import ContextualizedAgentEvent
from aihub_api.sockets.manager.dependencies.use_ws_manager import use_ws_manager_ws
from aihub_api.sockets.manager.WebSocketManager import WebSocketManager

logger = logging.getLogger(__name__)


class EventController(Controller):
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
                    detail="You do not have access to this thread. Please contact the process owner.",
                )

            return EventService.get_events_in_thread(
                locale=t.locale,
                thread_id=str_to_object_id(thread_id),
                display_id=str_to_object_id(display_id) if display_id else None,
            )

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
                        detail="You do not have access to this thread. Please contact the process owner.",
                    )

            return EventService.get_event_timeseries(
                time_range, agent_id=agent_id, agent_class=agent_class, event_name=event_name, thread_id=thread_id
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
