from typing import Callable, Any

from fastapi import APIRouter


def event_controller_factory(user_auth_strategy:  Callable[..., Any]):

    event_router = APIRouter()



    return event_router