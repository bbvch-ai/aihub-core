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

    def __init__(self, route: str = "/event", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_events(self, path: str = "/") -> "EventController":

        @self.router.get(path)
        async def get_all_events(
                user: AuthenticatedUser = Depends(self.auth),
        ) -> List[WSServerEvent]:
            return EventService.get_user_events(user.oid)

        return self

    def ws(self, path: str = "/ws") -> "EventController":

        @self.router.websocket(path)
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()  # Accept the connection first

            # Receive the first message which should contain the auth token
            first_message = await websocket.receive_json()
            token = first_message.get("token")[7:]

            if not token:
                await websocket.close(code=4000, reason="No token provided")
                return

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

            # If user is valid at this point:
            ws_manager = websocket.app.state.ws_manager
            ws_sender = websocket.app.state.ws_sender
            ws_receiver = websocket.app.state.ws_receiver

            logger.debug(f"User {user.oid} connected to websocket")
            await ws_manager.connect(websocket, user.oid)

            try:
                logger.debug(f"Receiving events for User {user.oid}")
                while True:
                    data = await websocket.receive_json()
                    logger.debug(f"Received data: {data}")
                    event = WSUserEvent.deserialize_event(data)

                    # Handle the event
                    await EventService.handle_ws_event(event, user.oid, ws_receiver, ws_sender)

            except WebSocketDisconnect as e:
                logging.error(f"Websocket disconnected: {e}")
                traceback.print_exc()
                logger.debug(f"User {user.oid} disconnected from websocket")
                await ws_manager.disconnect(user.oid)

        return self
