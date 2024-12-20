import logging
import traceback
from typing import Callable, Any, List

from fastapi import WebSocket, Depends, HTTPException
from starlette.websockets import WebSocketDisconnect

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.Controller import Controller
from api_core.sockets.events.server_to_user.WSServerEvent import WSServerEvent
from api_core.sockets.events.user_to_server.WSUserEvent import WSUserEvent

from .EventService import EventService
from ...auth.dependencies.oauth2.OAuth2Config import OAuth2Config

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

    ### Endpoints
    - `GET /event/`: Returns all events associated with the authenticated user.
    - `WEBSOCKET /event/ws`: Establishes a real-time, stateful connection allowing the client to send
      `WSUserEvent` messages and receive server updates (`WSServerEvent`), including errors and progress notifications.

    ### Authentication
    Events typically contain sensitive user or agent data. Authentication ensures only authorized users
    access their events and send commands over the WebSocket.

    ### Error Handling
    If the user is not authorized or the token is invalid, the WebSocket is closed with an appropriate code.
    Any exceptions are caught, and `ExceptionEvent` may be sent back to the client as feedback.
    """

    def __init__(self, route: str = "/event", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_events(self, path: str = "/") -> "EventController":

        @self.router.get(path)
        async def get_all_events(
                user: AuthenticatedUser = Depends(self.auth),
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
            If the token is valid, the user can send `WSUserEvent`s and receive responses (WSServerEvent or errors).
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
            except HTTPException as e:
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
            ws_receiver = websocket.app.state.ws_receiver

            logger.debug(f"User {user.oid} connected to websocket")
            await ws_manager.connect(websocket, user.oid)

            # Process incoming messages
            try:
                logger.debug(f"Receiving events for User {user.oid}")
                while True:
                    data = await websocket.receive_json()
                    logger.debug(f"Received data: {data}")
                    event = WSUserEvent.deserialize_event(data)

                    # Handle the received event
                    await EventService.handle_ws_event(event, user.oid, ws_receiver, ws_sender)

            except WebSocketDisconnect as e:
                logging.error(f"Websocket disconnected: {e}")
                traceback.print_exc()
                logger.debug(f"User {user.oid} disconnected from websocket")
                await ws_manager.disconnect(user.oid)

        return self
