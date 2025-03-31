import logging
import traceback
from typing import List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Security, WebSocket
from starlette.websockets import WebSocketDisconnect

from aihub_api.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from aihub_api.sockets.events.user_to_server import ExternalEvent

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
        async def get_all_events(
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[WSServerEvent]:
            """
            Returns all persisted events visible to the authenticated user.
            Useful for clients who want a snapshot of what has happened so far.
            """
            return EventService.get_user_events(user.oid)

        return self

    def ws(self, path: str = "/ws") -> "EventController":
        @self.router.websocket(path)
        async def websocket_endpoint(websocket: WebSocket):
            """
            Establishes a WebSocket connection. The first message must contain a token for authentication.
            If the token is valid, the user can send `ExternalEvent`s and receive responses (WSServerEvent or errors).
            """
            await websocket.accept()  # Accept the connection first

            # Receive initial auth message
            first_message = await websocket.receive_json()
            token = first_message.get("token")[7:]  # Extract token after "Bearer "

            if not token:
                await websocket.close(code=4000, reason="No token provided")
                return

            # Validate token
            try:
                user = await self.auth(token)
            except HTTPException:
                traceback.print_exc()
                await websocket.close(code=4001, reason="Invalid token")
                return
            except Exception as e:
                logger.exception(e)
                await websocket.close(code=4002, reason="Token validation error")
                return

            # User is authenticated at this point
            ws_manager = websocket.app.state.ws_manager
            ws_sender = websocket.app.state.ws_sender
            external_event_distributor = websocket.app.state.external_event_distributor

            logger.debug(f"User {user.oid} connected to websocket")
            await ws_manager.connect(websocket, user.oid)

            # Process incoming messages
            try:
                logger.debug(f"Receiving events for User {user.oid}")
                while True:
                    data = await websocket.receive_json()
                    logger.debug(f"Received data: {data}")
                    event = ExternalEvent.deserialize_event(data)

                    # Handle the received event
                    await EventService.handle_external_event(event, user.oid, external_event_distributor, ws_sender)

            except WebSocketDisconnect as e:
                logging.error(f"Websocket disconnected: {e}")
                traceback.print_exc()
                logger.debug(f"User {user.oid} disconnected from websocket")
                await ws_manager.disconnect(user.oid)

        return self
