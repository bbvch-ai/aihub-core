from fastapi import Request

from aihub_api.sockets.receiver.WebSocketReceiver import WebSocketReceiver


def use_ws_receiver(request: Request) -> WebSocketReceiver:
    return request.app.state.ws_receiver