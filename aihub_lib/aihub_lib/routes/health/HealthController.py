from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from aihub_lib.routes.health.dto.HealthResponse import HealthResponse


class HealthController(Controller):
    """
    A simple controller that provides a health check endpoint.

    ### Why HealthController?
    In production environments, load balancers, monitoring tools, or health checks
    need a straightforward way to confirm that the application is running and responsive.
    The `HealthController` offers a minimal endpoint (`/health`) that returns a simple "ok" status.

    ### Endpoint
    - `GET /health/`: Returns `{"status": "ok"}` if the application is healthy.

    ### Authentication
    No authentication is applied by default, as health checks are usually publicly accessible
    or controlled via infrastructure rules rather than application-level auth.

    ### Usage
    ```python
    app = FastAPI()
    HealthController().get_health().mount(app)
    ```

    Now calling `GET /health` returns a JSON response indicating the application status.
    """

    name = LocaleString(en="Health")
    description = LocaleString(en="Health Controller")
    icon = "solar:health-bold"

    def __init__(self, *, auth: AuthHandler, route: str = "/health", is_admin_only=True):
        super().__init__(auth=auth, route=route, is_admin_only=is_admin_only)

    def get_health(self, route: str = "/") -> "HealthController":
        @self.router.get(route, tags=self.tags)
        async def get_health() -> HealthResponse:
            """
            A simple health check endpoint that returns {"status": "ok"} if
            the application is running and capable of handling requests.
            """
            return HealthResponse(status="ok", code=200)

        return self
