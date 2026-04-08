from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.auth.keycloak.models.keycloak_group import KeycloakGroup
    from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser

__all__ = [
    "KeycloakGroup",
    "KeycloakUser",
]

_LAZY_IMPORTS = {
    "KeycloakGroup": "swiss_ai_hub.core.auth.keycloak.models.keycloak_group",
    "KeycloakUser": "swiss_ai_hub.core.auth.keycloak.models.keycloak_user",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
