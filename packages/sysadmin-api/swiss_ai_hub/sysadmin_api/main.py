# SPDX-License-Identifier: LicenseRef-Proprietary
# ruff: noqa: E402
# ASGI entrypoint: `swiss_ai_hub.sysadmin_api.main:app`. The fully-qualified
# module path avoids the `app.main:app` collision with packages/api (also
# installed into this image), which has its own top-level `app/` package.
from swiss_ai_hub.core.infrastructure import AihubInstrumentor

AihubInstrumentor().instrument()

from swiss_ai_hub.core.auth import TokenAndOauth2Handler
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.sysadmin_api import SysadminApiRunner, TenantAdminController, WhoamiController

enable_logging()


runner = SysadminApiRunner(
    title="Swiss AI Hub Sysadmin API",
    description="System administration plane — multi-tenant management endpoints.",
)
auth = TokenAndOauth2Handler.from_auth_settings()

runner.mount(
    HealthController(auth=auth).get_health(),
    WhoamiController(auth=auth).get_whoami(),
    TenantAdminController(auth=auth)
    .list_tenants()
    .list_unconfigured_tenants()
    .get_tenant()
    .create_tenant_metadata()
    .update_tenant_metadata()
    .delete_tenant_metadata(),
)

app = runner.create_app()
