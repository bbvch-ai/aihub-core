import logging
from typing import Dict, Set

from fastapi import WebSocket

from lib.records.WSEvents.WSServerEvent import WSServerEvent

logger = logging.getLogger(__name__)


class WebSocketManager:

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_threads: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        logger.debug(f"Connecting user {user_id}")
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        logger.debug(f"Disconnecting user {user_id}")
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_event(self, event: WSServerEvent, user_id: str):
        logger.debug(f"Sending event {event.model_dump()} to user {user_id}")
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(event.model_dump())
