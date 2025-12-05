from fastapi import Request, WebSocket
from nats.aio.client import Client as NATS
from nats.js import JetStreamContext


def use_nats(request: Request) -> NATS:
    return request.app.state.nc


def use_nats_ws(request: WebSocket) -> NATS:
    return request.app.state.nc


def use_nats_js(request: Request) -> JetStreamContext:
    return request.app.state.js
