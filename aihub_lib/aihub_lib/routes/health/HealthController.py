from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from aihub_lib.routes.health.dto.HealthResponse import HealthResponse


class HealthController(Controller):
    """
    A controller that provides a simple liveness health check endpoint.

    ### Why HealthController?
    In production environments, load balancers, monitoring tools, or health checks
    need a straightforward way to confirm that the application is running and responsive.

    ### Endpoints
    - `GET /health/`: Returns `{"status": "ok"}` if the application is alive (liveness probe).

    ### Authentication
    No authentication is applied by default, as health checks are usually publicly accessible
    or controlled via infrastructure rules rather than application-level auth.

    ### Usage
    ```python
    HealthController(auth=auth).get_health().mount(app)
    ```

    For readiness checks with dependency verification, extend this controller
    in your service package with service-specific health checks.
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
