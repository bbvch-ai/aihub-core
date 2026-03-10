from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.auth.access.AccessChecker import AccessChecker
    from swiss_ai_hub.core.auth.access.AccessLevel import AccessLevel
    from swiss_ai_hub.core.auth.dependencies.AuthHandler import AuthHandler
    from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
        DangerousDevelopmentOnlyAuthHandler,
    )
    from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
        DangerousDevelopmentOnlyAuthSettings,
    )
    from swiss_ai_hub.core.auth.dependencies.SuperuserAuthHandler.SuperuserSettings import SuperuserSettings
    from swiss_ai_hub.core.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
    from swiss_ai_hub.core.auth.identity.TenantIdentity import TenantIdentity
    from swiss_ai_hub.core.auth.identity.UserIdentity import UserIdentity

# KeycloakAuthHandler and TokenAndOauth2Handler are excluded because KeycloakAuthHandler
# instantiates KeycloakSettings() at class definition time, requiring KEYCLOAK_URL to be set.
# Import them directly:
#   from swiss_ai_hub.core.auth.dependencies.KeycloakAuthHandler.KeycloakAuthHandler import KeycloakAuthHandler
#   from swiss_ai_hub.core.auth.dependencies.TokenAndOauth2Handler.TokenAndOauth2Handler import TokenAndOauth2Handler

__all__ = [
    "AccessChecker",
    "AccessLevel",
    "AuthHandler",
    "DangerousDevelopmentOnlyAuthHandler",
    "DangerousDevelopmentOnlyAuthSettings",
    "SuperuserSettings",
    "TenantIdentity",
    "TokenAuthHandler",
    "UserIdentity",
]

_LAZY_IMPORTS = {
    "AccessChecker": "swiss_ai_hub.core.auth.access.AccessChecker",
    "AccessLevel": "swiss_ai_hub.core.auth.access.AccessLevel",
    "AuthHandler": "swiss_ai_hub.core.auth.dependencies.AuthHandler",
    "DangerousDevelopmentOnlyAuthHandler": "swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler",
    "DangerousDevelopmentOnlyAuthSettings": "swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings",
    "SuperuserSettings": "swiss_ai_hub.core.auth.dependencies.SuperuserAuthHandler.SuperuserSettings",
    "TenantIdentity": "swiss_ai_hub.core.auth.identity.TenantIdentity",
    "TokenAuthHandler": "swiss_ai_hub.core.auth.dependencies.TokenAuthHandler.TokenAuthHandler",
    "UserIdentity": "swiss_ai_hub.core.auth.identity.UserIdentity",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
