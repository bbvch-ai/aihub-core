from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.dependencies.KeycloakAuthHandler.KeycloakAuthHandler import KeycloakAuthHandler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler


def resolve_auth_strategy(auth_strategy: str) -> AuthHandler:
    if auth_strategy == "NoAuth":
        return DangerousDevelopmentOnlyAuthHandler()
    elif auth_strategy == "TokenAuth":
        return TokenAuthHandler()
    elif auth_strategy == "KeycloakAuth":
        return KeycloakAuthHandler()
    else:
        raise ValueError(f"Unknown auth strategy: {auth_strategy}")
