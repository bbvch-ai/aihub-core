from fastapi import Request, WebSocket


from aihub_api.sockets.sender.WebSocketSender import WebSocketSender


def use_ws_sender(request: Request) -> WebSocketSender:
    return request.app.state.ws_sender

def use_ws_sender_ws(request: WebSocket) -> WebSocketSender:
    return request.app.state.ws_sender