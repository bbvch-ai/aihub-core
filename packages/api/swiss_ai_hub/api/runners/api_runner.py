import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Self, override

from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.metrics import NoOpMeterProvider
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.routes import Controller
from swiss_ai_hub.core.runners import OpenApiSchemaService, Runner

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.i18n.middleware.i18n_middleware import I18nMiddleware
from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.routes.process.process_controller import ProcessController
from swiss_ai_hub.api.runners.lifetime.lifetime_manager import lifetime_manager

logger = logging.getLogger(__name__)

# Bounded allowlist of request headers captured as span attributes. Capturing every
# header ([".*"]) added high-cardinality attributes (user-agent, traceparent, cookie,
# content-length) that inflated trace/metric cardinality — see issue #1496.
CAPTURED_REQUEST_HEADERS = ["content-type", "accept", "accept-language"]


class ApiRunner(Runner):
    """
    A concrete implementation of Runner for standard API services with
    internationalization and CORS support.

    ### Why Use ApiRunner?
    `ApiRunner` extends the base `Runner` class with specific features for standard HTTP APIs:
    - Configures CORS middleware with sensible defaults
    - Integrates internationalization (i18n) for API responses
    - Applies tag-based OpenAPI documentation organization
    - Provides a lifecycle manager tailored for API services

    ### Key Features
    - **CORS Configuration:** Automatically configures Cross-Origin Resource Sharing with
      appropriate origins from configuration.
    - **Internationalization:** Integrates with `I18nMiddleware` for multilingual support.
    - **Enhanced Documentation:** Generates OpenAPI tags and descriptions from controllers.
    - **Lifecycle Management:** Uses the API-specific lifetime manager.

    ### Usage
    ```python
    runner = ApiRunner(api_path="/api/v1", title="My API")
    runner.mount(UserController(), ProductController())  # Mount controllers
    app = runner.create_app()  # Get the FastAPI instance
    ```

    Run the resulting `app` using `uvicorn` or another ASGI server.
    """

    def __init__(
        self,
        api_path: str = "/api/v1",
        title: str = "AI Hub",
        description: str = "AI Hub Backend",
        origins: list[str] | None = None,
    ):
        super().__init__(api_path, title, description, origins)

    @property
    def lifetime_manager(self) -> Callable[[FastAPI], AbstractAsyncContextManager]:
        return lifetime_manager

    @override
    def create_app(self) -> Starlette:
        mcp = FastMCP.from_fastapi(
            app=self._api_app,
            route_maps=[
                RouteMap(methods=["GET"], pattern=r".*\{.*\}.*", mcp_type=MCPType.RESOURCE_TEMPLATE),
                RouteMap(methods=["GET"], pattern=r".*", mcp_type=MCPType.RESOURCE),
                RouteMap(methods=["POST"], pattern=r".*", mcp_type=MCPType.EXCLUDE),
                RouteMap(methods=["PUT"], pattern=r".*", mcp_type=MCPType.EXCLUDE),
                RouteMap(methods=["PATCH"], pattern=r".*", mcp_type=MCPType.EXCLUDE),
                RouteMap(methods=["DELETE"], pattern=r".*", mcp_type=MCPType.EXCLUDE),
            ],
        )
        mcp_app = mcp.http_app(path="/")

        @asynccontextmanager
        async def combined_lifespan(app):
            # Start API lifespan first
            api_lifespan = self.lifetime_manager(self._api_app)

            async with api_lifespan:
                # Then start MCP lifespan
                mcp_lifespan = mcp_app.lifespan(mcp_app)
                async with mcp_lifespan:
                    yield

        app = Starlette(
            routes=[
                Mount(self.api_path, app=self._api_app),
                Mount("/mcp", app=mcp_app),
            ],
            lifespan=combined_lifespan,
        )

        app.state.api_app = self._api_app
        for controller in self.controllers:
            if isinstance(controller, AgentController):
                app.state.agent_controller = controller

            if isinstance(controller, ProcessController):
                app.state.process_controller = controller

        self._api_app.state = app.state
        mcp_app.state = app.state

        prometheus_registry = self._configure_opentelemetry()
        if prometheus_registry is not None:
            app.routes.append(self._build_metrics_route(prometheus_registry))
            logger.info("Prometheus scrape endpoint served at /metrics")

        return app

    def _get_api_app(self) -> FastAPI:
        """
        Creates the API FastAPI application that will be mounted under `api_path`.
        Applies middleware like CORS and i18n. The controllers are mounted onto this app.
        """
        app = super()._get_api_app()

        # Custom OpenAPI schema hook to inject tenant_id path parameter
        original_openapi = app.openapi

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema
            schema = original_openapi()
            app.openapi_schema = OpenApiSchemaService.inject_tenant_id_into_openapi(schema)
            return app.openapi_schema

        app.openapi = custom_openapi  # type: ignore[method-assign]

        origins = self.origins or ["http://localhost:8080"]
        if AIHubSettings().FRONTEND_ORIGIN:
            origins += [item.strip() for item in AIHubSettings().FRONTEND_ORIGIN.split(",")]

        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.ai-agents\.ch",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Internationalization middleware
        app.add_middleware(I18nMiddleware)
        return app

    def mount(self, *controllers: Controller) -> Self:
        """
        Mounts one or more controllers onto the API application.

        Controllers extending ``TenantScopedController`` are mounted under
        ``/{tenant_id}/<route>``. Global controllers (``Controller``, including
        ``HealthController``) are mounted at their base route without a tenant prefix.
        """
        super().mount(*controllers)

        existing_tag_names = {tag["name"] for tag in (self._api_app.openapi_tags or [])}
        new_tags = [
            {
                "name": ApiLocaleHandler().extract(controller.name, locale="en"),
                "description": ApiLocaleHandler().extract(controller.description, locale="en"),
            }
            for controller in controllers
        ]
        self._api_app.openapi_tags = (self._api_app.openapi_tags or []) + [
            tag for tag in new_tags if tag["name"] not in existing_tag_names
        ]

        # Pre-populate state with controller references so they're available
        # before create_app() is called (needed for SimulatedAgentApiTestRunner)
        for controller in controllers:
            if isinstance(controller, AgentController):
                self._api_app.state.agent_controller = controller
            if isinstance(controller, ProcessController):
                self._api_app.state.process_controller = controller

        return self

    def _configure_opentelemetry(self) -> CollectorRegistry | None:
        """
        Configure FastAPI-specific OpenTelemetry instrumentation.

        Returns the registry backing the scrape endpoint when Prometheus metrics are enabled, so
        create_app() knows whether to serve /metrics; None otherwise.
        """
        from swiss_ai_hub.core.infrastructure import OpenTelemetrySettings

        otel_settings = OpenTelemetrySettings()

        if not otel_settings.ENABLED:
            logger.info("OpenTelemetry instrumentation disabled: OTEL_ENABLED=False")
            return None

        # Metrics are a separate opt-in from tracing (OTEL_METRICS_ENABLED, default off): the
        # FastAPI/ASGI auto-instrumentation's request-count/duration histograms were the
        # unbounded, high-cardinality metric source behind issue #1496. configure_metrics()
        # returns None (NoOpMeterProvider fallback) unless explicitly enabled.
        #
        # A registry per app instance, never prometheus_client's global REGISTRY: the test suite
        # builds many apps in one process, and a shared registry raises "Duplicated timeseries"
        # on the second one.
        prometheus_registry = CollectorRegistry() if otel_settings.METRICS_ENABLED else None
        meter_provider = otel_settings.configure_metrics(prometheus_registry) or NoOpMeterProvider()

        FastAPIInstrumentor.instrument_app(
            self._api_app,
            exclude_spans=["receive", "send"],
            http_capture_headers_server_request=CAPTURED_REQUEST_HEADERS,
            meter_provider=meter_provider,
        )
        logger.info("FastAPI application instrumented with OpenTelemetry")
        logger.info("Note: Core OpenTelemetry, MongoDB, and HTTP client configuration handled in lifetime_manager")

        return prometheus_registry

    @staticmethod
    def _build_metrics_route(registry: CollectorRegistry) -> Route:
        """
        Serve the scrape endpoint on the OUTER Starlette app, deliberately not under api_path.

        Three consequences follow from that placement, all of them wanted: Traefik routes the API
        on PathPrefix(`/api/v1`) only, so /metrics is unreachable from the internet and stays a
        cluster-internal target; FastMCP.from_fastapi() turns every GET on the inner app into an
        MCP resource, which this must not become; and the inner app's auth and i18n middleware
        never runs for a scraper that carries no token and no Accept-Language.
        """

        async def serve_metrics(_: Request) -> Response:
            return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

        return Route("/metrics", serve_metrics, methods=["GET"])
