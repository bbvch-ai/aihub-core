from fastapi import Request
from nats.aio.client import Client as NATS


def use_nats(request: Request) -> NATS:
    return request.app.state.nc
