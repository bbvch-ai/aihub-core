from typing import Callable, Any

from aihub_api.routes.Controller import Controller


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

    def __init__(self, route: str = "/health", auth: Callable[..., Any] = None):
        super().__init__(route, auth)

    def get_health(self, route: str = "/") -> "HealthController":
        @self.router.get(route)
        async def get_health() -> dict[str, str]:
            """
            A simple health check endpoint that returns {"status": "ok"} if
            the application is running and capable of handling requests.
            """
            return {"status": "ok"}
        return self
