from fastapi import Request, WebSocket
from nats.aio.client import Client as NATS


def use_nats(request: Request) -> NATS:
    return request.app.state.nc


def use_nats_ws(request: WebSocket) -> NATS:
    return request.app.state.nc
