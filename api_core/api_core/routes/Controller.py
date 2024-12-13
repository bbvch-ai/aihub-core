import abc
from typing import Callable, Any

from fastapi import APIRouter

from api_core.auth.dependencies.no_auth.use_no_auth_user import use_no_auth_user


class Controller(abc.ABC):

    def __init__(self, route: str, user_auth_strategy: Callable[..., Any] = None):
        self.base_route = route
        self.user_auth_strategy = user_auth_strategy or use_no_auth_user
        self.router = APIRouter()

