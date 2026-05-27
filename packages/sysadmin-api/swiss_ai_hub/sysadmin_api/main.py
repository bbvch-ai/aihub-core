# SPDX-License-Identifier: LicenseRef-Proprietary
# ruff: noqa: E402
# ASGI entrypoint: `swiss_ai_hub.sysadmin_api.main:app`. The fully-qualified
# module path avoids the `app.main:app` collision with packages/api (also
# installed into this image), which has its own top-level `app/` package.
from swiss_ai_hub.core.infrastructure import AihubInstrumentor

AihubInstrumentor().instrument()

from swiss_ai_hub.api import AuthProviderController, MyAccountController, RoleController, UserController
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
    # Controllers from packages/api re-mounted here so sysadmin-web's inherited
    # @swiss-ai-hub/web composables resolve same-origin against sysadmin-api,
    # letting the sysadmin plane run as a self-contained product slice (no main
    # API required). Code ownership stays in packages/api; sysadmin-api only
    # picks the surface it needs.
    #
    # MyAccountController only registers ``get_my_identity()`` — the identity-only
    # split — because ``get_my_account`` returns an access matrix enumerated from
    # ``runner.controllers``, which on sysadmin-api would be a misleadingly
    # narrow subset of the platform surface. The middleware-relevant ``is_sys_admin``
    # field lives on the identity DTO already.
    MyAccountController(auth=auth).get_my_identity(),
    UserController(auth=auth).get_user().get_users(),
    RoleController(auth=auth).get_role().get_roles().create_role().update_role().delete_role(),
    AuthProviderController(auth=auth).get_auth_providers(),
)

app = runner.create_app()
