import abc
import logging
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from opentelemetry import trace

from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners.runner import Runner

logger = logging.getLogger(__name__)


class Controller(abc.ABC):
    """
    A base class for controllers that define API endpoints in a structured and consistent way.

    ### Why This Class?
    In a typical FastAPI application, you might have multiple routers spread across different modules.
    By subclassing `Controller`, you establish a convention:
    - Each controller corresponds to a base route.
    - Each controller can define its own authentication dependencies.

    This makes it easier to:
    - Keep routes organized in separate classes.
    - Apply common authentication or middleware logic at the controller level.
    - Mount all controllers onto the main application in a uniform manner.

    ### Key Features
    - `base_route`: The base path under which this controller’s endpoints will be accessible.
    - `auth`: A dependency (or set of dependencies) for authentication/authorization. Defaults to `use_no_auth_user`,
      meaning no authentication is applied unless overridden.

    ### Example
    ```python
    class MyController(Controller):
        def __init__(self):
            super().__init__(route="/my-endpoints", auth=some_auth_dependency)
            # define endpoints using self.router.get(), etc.

    app = FastAPI()
    controller = MyController()
    controller.mount(app)
    ```

    This sets up all routes defined in `MyController` under `/my-endpoints`.
    """

    name = LocaleString.from_i18n_path("lib.controllers.base.name")
    description = LocaleString.from_i18n_path("lib.controllers.base.description")
    icon = "mage:server"  # https://icon-sets.iconify.design/

    def __init__(self, *, auth: AuthHandler, route: str, additionally_required_permission: str | None = None):
        self.base_route: str = route
        self.auth: AuthHandler = auth
        self.router: APIRouter = APIRouter()
        self.additionally_required_permission = additionally_required_permission
        self._runner: Runner | None = None

    @property
    def service_name(self):
        return self.__class__.__name__.lower().replace("controller", "")

    def authenticated_user(self):
        """Return a dependency that only authenticates — no tenant or permission checks.

        Use this for global (non-tenant-scoped) endpoints that need a logged-in user
        but don't operate within a tenant context.
        """

        def check_authenticated(
            request: Request,
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> UserIdentity:
            self._enrich_span_with_context(user, request, "authenticated")
            return user

        return check_authenticated

    def sys_admin_user(self):
        """Return a dependency that authenticates and requires the ``AIHubSysAdmin`` realm role.

        Use for global sysadmin-only endpoints. Relies on ``UserIdentity.is_sys_admin``,
        which is populated from the JWT ``roles`` claim by ``KeycloakAuthHandler``.
        """

        def check_sys_admin(
            request: Request,
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> UserIdentity:
            if not user.is_sys_admin:
                logger.warning("User %s attempted sysadmin access without the required role", user.email)
                raise HTTPException(status_code=403, detail="Forbidden: Requires the AIHubSysAdmin role.")
            self._enrich_span_with_context(user, request, "sys_admin")
            return user

        return check_sys_admin

    def user_with_permission(self, permission_template: str):
        def check_access(
            request: Request,
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> UserIdentity:
            required_permission = permission_template.format(**request.path_params)

            access_checker = AccessChecker.from_user(user)

            if not access_checker.has_access_to_service(self.service_name):
                logger.warning(
                    f"User {user.email} does not have access to service {self.service_name}. "
                    f"Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the permission to access the {self.service_name}-service.",
                )

            if self.additionally_required_permission and not access_checker.has_access(
                self.additionally_required_permission
            ):
                logger.warning(
                    f"User {user.email} does not have special permission {self.additionally_required_permission}. "
                    f"Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the required additional "
                    f"'{self.additionally_required_permission}' permission to access this service.",
                )

            if not access_checker.has_access(required_permission):
                logger.warning(
                    f"User {user.email} does not have permission {required_permission}. "
                    f"Got roles {user.roles} with access rules {access_checker.access_rules}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Forbidden: You do not have the required '{required_permission}' permission.",
                )

            self._enrich_span_with_context(user, request, required_permission)

            return user

        return check_access

    def _enrich_span_with_context(self, user: UserIdentity, request: Request, required_permission: str) -> None:
        """Enrich the current OpenTelemetry span with rich contextual information."""
        span = trace.get_current_span()

        if not span.is_recording():
            return

        span.set_attribute("user.id", user.id)
        span.set_attribute("user.email", user.email)
        span.set_attribute("user.display_name", user.name)
        if user.roles:
            span.set_attribute("user.roles", ",".join(user.roles))

        # Service context
        span.set_attribute("service.controller", self.service_name)
        span.set_attribute("auth.required_permission", required_permission)

        # Tenant context (use resolved tenant, not raw path param which may be "active")
        if user.acting_within_tenant:
            span.set_attribute("tenant.id", user.acting_within_tenant.id)

        # Path parameters (business context)
        if request.path_params:
            for param_name, param_value in request.path_params.items():
                if param_name == "tenant_id":
                    continue
                elif param_name in ["agent_class", "agent_id", "thread_id", "process_id", "process_class"]:
                    span.set_attribute(f"{param_name.replace('_', '.')}", str(param_value))
                else:
                    span.set_attribute(f"resource.{param_name}", str(param_value))

        # Record the concrete path on http.target; never overwrite http.route, which the
        # FastAPI instrumentation keeps as the bounded route template. De-templating it
        # exploded metric/label cardinality (one series per URL) — see issue #1496.
        span.set_attribute("http.target", request.url.path)
        if client_host := getattr(request.client, "host", None):
            span.set_attribute("client.ip", client_host)

    @property
    def tags(self):
        return [LocaleHandler().extract(self.name, locale="en")]

    def mount(self, app: FastAPI, runner: "Runner"):
        """
        Attach this controller’s router to the given FastAPI application using the base_route prefix.
        This final step exposes all endpoints defined in this controller to incoming requests.
        """
        app.include_router(self.router, prefix=self.base_route)
        self._runner = runner
