from fastapi import Request, WebSocket

from swiss_ai_hub.api.sockets.manager.web_socket_manager import WebSocketManager


def use_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager


def use_ws_manager_ws(request: WebSocket) -> WebSocketManager:
    return request.app.state.ws_manager
