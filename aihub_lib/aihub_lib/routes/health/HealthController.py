from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Request, Response
from starlette.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from aihub_lib.routes.health.dto.HealthResponse import HealthResponse

HealthChecker = Callable[[Request], Awaitable[bool]]


class HealthController(Controller):
    """
    A controller that provides health check endpoints for liveness and readiness probes.

    ### Why HealthController?
    In production environments, load balancers, monitoring tools, or health checks
    need a straightforward way to confirm that the application is running and responsive.
    The `HealthController` offers endpoints for both liveness and readiness checks.

    ### Endpoints
    - `GET /health/`: Returns `{"status": "ok"}` if the application is alive (liveness probe).
    - `GET /health/ready`: Returns detailed status with dependency checks (readiness probe).

    ### Authentication
    No authentication is applied by default, as health checks are usually publicly accessible
    or controlled via infrastructure rules rather than application-level auth.

    ### Usage
    ```python
    # Simple usage (liveness only)
    HealthController(auth=auth).get_health().mount(app)

    # With readiness checks
    async def check_nats(request: Request) -> bool:
        return hasattr(request.app.state, 'nc') and request.app.state.nc.is_connected

    HealthController(auth=auth).get_health().get_ready(checkers={"nats": check_nats}).mount(app)
    ```
    """

    name = LocaleString(en="Health")
    description = LocaleString(en="Health Controller")
    icon = "solar:health-bold"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/health", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_health(self, route: str = "/") -> "HealthController":
        @self.router.get(route, tags=self.tags)
        async def get_health() -> HealthResponse:
            """
            A simple liveness check endpoint that returns {"status": "ok"} if
            the application is running and capable of handling requests.
            """
            return HealthResponse(status="ok", code=200)

        return self

    def get_ready(
        self,
        route: str = "/ready",
        checkers: Annotated[dict[str, HealthChecker] | None, "Health check functions keyed by name"] = None,
    ) -> "HealthController":
        """
        Adds a readiness check endpoint that runs all provided health checkers.

        The endpoint returns 200 if all checks pass, 503 if any check fails.
        """
        health_checkers = checkers or {}

        @self.router.get(route, tags=self.tags)
        async def get_ready(request: Request, response: Response) -> HealthResponse:
            """
            A readiness check endpoint that verifies all dependencies are available.
            Returns detailed check results for monitoring and debugging.
            """
            checks: dict[str, bool] = {}
            all_healthy = True

            for name, checker in health_checkers.items():
                try:
                    result = await checker(request)
                    checks[name] = result
                    if not result:
                        all_healthy = False
                except Exception:
                    checks[name] = False
                    all_healthy = False

            status = "ok" if all_healthy else "unhealthy"
            code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
            response.status_code = code

            return HealthResponse(status=status, code=code, checks=checks)

        return self
