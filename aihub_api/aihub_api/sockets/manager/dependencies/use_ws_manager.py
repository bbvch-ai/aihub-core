from fastapi import Request, WebSocket

from aihub_api.sockets.manager.WebSocketManager import WebSocketManager


def use_ws_manager(request: Request) -> WebSocketManager:
    return request.app.state.ws_manager

def use_ws_manager_ws(request: WebSocket) -> WebSocketManager:
    return request.app.state.ws_manager