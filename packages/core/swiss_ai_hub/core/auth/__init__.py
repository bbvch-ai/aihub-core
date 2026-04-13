from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
    from swiss_ai_hub.core.auth.access.access_level import AccessLevel
    from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
    from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (  # noqa: E501
        DangerousDevelopmentOnlyAuthHandler,
    )
    from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
        DangerousDevelopmentOnlyAuthSettings,
    )
    from swiss_ai_hub.core.auth.dependencies.superuser_auth_handler.superuser_settings import SuperuserSettings
    from swiss_ai_hub.core.auth.dependencies.token_and_oauth2_handler.token_and_oauth2_handler import (
        TokenAndOauth2Handler,
    )
    from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
    from swiss_ai_hub.core.auth.identity.sys_admin_identity import SysAdminIdentity
    from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
    from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
    from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
    from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
    from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
    from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser

# KeycloakAuthHandler, TokenAndOauth2Handler, and SysAdminAuthHandler are excluded because they
# instantiate KeycloakSettings() at class definition time, requiring KEYCLOAK_URL to be set.
# Import them directly:
#   from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler
#   from swiss_ai_hub.core.auth.dependencies.token_and_oauth2_handler.token_and_oauth2_handler import TokenAndOauth2Handler
#   from swiss_ai_hub.core.auth.dependencies.sys_admin_auth_handler.sys_admin_auth_handler import SysAdminAuthHandler

__all__ = [
    "TokenAndOauth2Handler",
    "AccessChecker",
    "AccessLevel",
    "AuthHandler",
    "DangerousDevelopmentOnlyAuthHandler",
    "DangerousDevelopmentOnlyAuthSettings",
    "KeycloakAdminService",
    "KeycloakGroup",
    "KeycloakSettings",
    "KeycloakUser",
    "SuperuserSettings",
    "SysAdminIdentity",
    "TenantIdentity",
    "TokenAuthHandler",
    "UserIdentity",
]

_LAZY_IMPORTS = {
    "TokenAndOauth2Handler": "swiss_ai_hub.core.auth.dependencies.token_and_oauth2_handler.token_and_oauth2_handler",
    "AccessChecker": "swiss_ai_hub.core.auth.access.access_checker",
    "AccessLevel": "swiss_ai_hub.core.auth.access.access_level",
    "AuthHandler": "swiss_ai_hub.core.auth.dependencies.auth_handler",
    "KeycloakAdminService": "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service",
    "KeycloakGroup": "swiss_ai_hub.core.auth.keycloak.models.keycloak_group",
    "KeycloakSettings": "swiss_ai_hub.core.auth.keycloak.keycloak_settings",
    "KeycloakUser": "swiss_ai_hub.core.auth.keycloak.models.keycloak_user",
    "DangerousDevelopmentOnlyAuthHandler": "swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler",  # noqa: E501
    "DangerousDevelopmentOnlyAuthSettings": "swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings",  # noqa: E501
    "SuperuserSettings": "swiss_ai_hub.core.auth.dependencies.superuser_auth_handler.superuser_settings",
    "SysAdminIdentity": "swiss_ai_hub.core.auth.identity.sys_admin_identity",
    "TenantIdentity": "swiss_ai_hub.core.auth.identity.tenant_identity",
    "TokenAuthHandler": "swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler",
    "UserIdentity": "swiss_ai_hub.core.auth.identity.user_identity",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
