from nats.aio.client import Client as NATS
from fastapi import Request

def use_nats(request: Request) -> NATS:
    return request.app.state.nc