# SPDX-License-Identifier: LicenseRef-Proprietary
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller import TenantAdminController
    from swiss_ai_hub.sysadmin_api.routes.whoami.whoami_controller import WhoamiController

__all__ = [
    "TenantAdminController",
    "WhoamiController",
]

_LAZY_IMPORTS: dict[str, str] = {
    "TenantAdminController": "swiss_ai_hub.sysadmin_api.routes.tenant_admin.tenant_admin_controller",
    "WhoamiController": "swiss_ai_hub.sysadmin_api.routes.whoami.whoami_controller",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
