from typing import Callable, Any

from api_core.routes.Controller import Controller


class HealthController(Controller):

    def __init__(self, route: str = "/health", user_auth_strategy: Callable[..., Any] = None):
        super().__init__(route, user_auth_strategy)

    def get_health(self, route: str = "/") -> "HealthController":
        @self.router.get(route)
        async def get_health() -> dict[str, str]:
            return {"status": "ok"}
        return self