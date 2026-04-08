from typing import TYPE_CHECKING

from fastapi import FastAPI

from swiss_ai_hub.core.routes.controller import Controller

if TYPE_CHECKING:
    from swiss_ai_hub.core.runners.runner import Runner

TENANT_PATH_PREFIX = "/{tenant_id}"


class TenantScopedController(Controller):
    """A controller whose routes are scoped under a ``/{tenant_id}`` path prefix.

    All endpoints defined on subclasses will be mounted at
    ``/{tenant_id}/<base_route>/<endpoint>``. The ``tenant_id`` path parameter is
    injected into the OpenAPI spec via a custom schema hook in ``ApiRunner``.
    """

    def mount(self, app: FastAPI, runner: "Runner"):
        app.include_router(self.router, prefix=TENANT_PATH_PREFIX + self.base_route)
        self._runner = runner
