import logging
from typing import Annotated, List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor_ws
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import EVENT_TIMESERIES_TIME_RANGE
from aihub_lib.persistence.utils import str_to_object_id
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Security, WebSocket
from fastapi.params import Path, Query

from aihub_api.sockets.events.server_to_user.WSServerEvent import WSServerEvent

from ...i18n.dependencies.use_locale import use_locale, use_locale_ws
from ...sockets.manager.dependencies.use_ws_manager import use_ws_manager_ws
from ...sockets.manager.WebSocketManager import WebSocketManager
from ...sockets.sender.dependencies.use_ws_sender import use_ws_sender_ws
from ...sockets.sender.WebSocketSender import WebSocketSender
from .dto.EventTimeseries import EventTimeseries
from .EventService import EventService

logger = logging.getLogger(__name__)


class EventController(Controller):
    """
    A controller that manages the event-related endpoints, including:
    - Retrieving a user’s persisted events.
    - Establishing a WebSocket connection for real-time two-way messaging.

    ### Why EventController?
    In interactive systems, clients often need to:
    - Fetch historical events (e.g., from past sessions or previous steps in a workflow).
    - Maintain a live WebSocket connection for sending commands and receiving updates in real-time.

    The `EventController` provides HTTP and WebSocket endpoints to handle these use cases.
    """

    name = LocaleString(en="Events")
    description = LocaleString(en="Inspect events in the system")
    icon = "mdi:apache-kafka"

    def __init__(self, route: str = "/event", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def get_events(self, path: str = "/") -> "EventController":
        @self.router.get(path, tags=self.tags)
        async def get_events(
            thread_id: Annotated[str, Query(pattern="^[a-f0-9]{24}$")] = None,
            display_id: Annotated[str, Query(pattern="^[a-f0-9]{24}$")] = None,
            event_class: Annotated[str, Query()] = None,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> List[WSServerEvent]:
            """
            Returns all persisted events visible to the authenticated user.
            Useful for clients who want a snapshot of what has happened so far.
            """
            if display_id is not None and thread_id is None:
                raise HTTPException(
                    status_code=400, detail="If display_id is provided, thread_id must also be provided."
                )
            return EventService.get_user_events(
                user.oid,
                t.locale,
                str_to_object_id(thread_id) if thread_id else None,
                str_to_object_id(display_id) if display_id else None,
                event_class,
            )

        return self

    def get_events_in_thread(self, path: str = "/thread/{thread_id}") -> "EventController":
        @self.router.get(path, tags=self.tags)
        async def get_events_in_thread(
            thread_id: Annotated[str, Path(title="Thread ID", pattern="^[a-f0-9]{24}$")],
            display_id: Annotated[str, Query(pattern="^[a-f0-9]{24}$")] = None,
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> List[WSServerEvent]:
            """
            Returns all events in a given thread
            """
            if display_id is not None and thread_id is None:
                raise HTTPException(
                    status_code=400, detail="If display_id is provided, thread_id must also be provided."
                )
            return EventService.get_user_events(
                user.oid,
                t.locale,
                str_to_object_id(thread_id),
                str_to_object_id(display_id) if display_id else None,
            )

        return self

    def ws(self, path: str = "/ws") -> "EventController":
        @self.router.websocket(path)
        async def websocket_endpoint(
            websocket: WebSocket,
            external_event_distributor: Annotated[ExternalEventDistributor, Depends(use_external_event_distributor_ws)],
            ws_sender: Annotated[WebSocketSender, Depends(use_ws_sender_ws)],
            ws_manager: Annotated[WebSocketManager, Depends(use_ws_manager_ws)],
            t: Annotated[LocaleHandler, Depends(use_locale_ws)],
        ):
            """
            Establishes a WebSocket connection. The first message must contain a token for authentication.
            If the token is valid, the user can send `ExternalEvent`s and receive responses (WSServerEvent or errors).
            """
            await websocket.accept()  # Accept the connection first

            # Receive initial auth message
            first_message = await websocket.receive_json()
            token = first_message.get("token")

            # Handle "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]  # Extract token after "Bearer "

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
                ws_sender,
                ws_manager,
                external_event_distributor,
                user,
                t,
            )

        return self

    def get_event_timeseries(self, route: str = "/timeseries/{time_range}") -> "EventController":
        @self.router.get(route, tags=self.tags)
        async def get_event_timeseries(
            time_range: Annotated[
                EVENT_TIMESERIES_TIME_RANGE,
                Path(
                    title="Time Range",
                    description="Time range for the statistics (1h, 24h, 30d, 365d)",
                ),
            ],
            thread_id: Annotated[str, Query()] = None,
            agent_id: Annotated[str, Query(title="Agent ID")] = None,
            agent_class: Annotated[str, Query(title="Agent Class")] = None,
            event_name: Annotated[str, Query(title="Event Name")] = None,
            user: AuthenticatedUser = Security(self.auth),
        ) -> EventTimeseries:
            """
            Retrieves time-based statistics.
            Returns event counts in time buckets with resolution based on the time range:
            - 1h: 1 minute resolution
            - 24h: 1 hour resolution
            - 30d: 1 day resolution
            - 365d: 1 week resolution
            """
            return EventService.get_event_timeseries(
                time_range, agent_id=agent_id, agent_class=agent_class, event_name=event_name, thread_id=thread_id
            )

        return self
