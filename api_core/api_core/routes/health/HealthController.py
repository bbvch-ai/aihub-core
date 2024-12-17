from typing import Callable, Any

from api_core.routes.Controller import Controller


class HealthController(Controller):

    def __init__(self, route: str = "/health", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_health(self, route: str = "/") -> "HealthController":
        @self.router.get(route)
        async def get_health() -> dict[str, str]:
            return {"status": "ok"}
        return self