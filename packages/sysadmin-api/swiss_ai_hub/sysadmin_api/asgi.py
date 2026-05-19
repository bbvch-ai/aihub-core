# ruff: noqa: E402
# Fully-qualified ASGI entrypoint: `swiss_ai_hub.sysadmin_api.asgi:app`.
# Deliberately NOT `app.main` — packages/api also ships an `app/main.py`, and a
# bare `app.main` target is a module-name collision footgun once both packages
# are present in the same image (sysadmin-api bundles swiss-ai-hub-api).
from swiss_ai_hub.core.infrastructure import AihubInstrumentor

AihubInstrumentor().instrument()

from swiss_ai_hub.core.auth import TokenAndOauth2Handler
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.routes import HealthController

from swiss_ai_hub.sysadmin_api import SysadminApiRunner, TenantAdminController

enable_logging()


runner = SysadminApiRunner(
    title="Swiss AI Hub Sysadmin API",
    description="System administration plane — multi-tenant management endpoints.",
)
auth = TokenAndOauth2Handler.from_auth_settings()

runner.mount(
    HealthController(auth=auth).get_health(),
    TenantAdminController(auth=auth)
    .list_tenants()
    .list_unconfigured_tenants()
    .get_tenant()
    .create_tenant_metadata()
    .update_tenant_metadata()
    .delete_tenant_metadata(),
)

app = runner.create_app()
