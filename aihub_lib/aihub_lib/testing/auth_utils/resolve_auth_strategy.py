from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.AzureIdentityProvider.AzureIdentityProvider import AzureIdentityProvider
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.auth.identity.TokenIdentityProvider.TokenIdentityProvider import TokenIdentityProvider


def resolve_auth_strategy(auth_strategy: str) -> AuthHandler:
    if auth_strategy == "NoAuth":
        return DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    elif auth_strategy == "TokenAuth":
        return TokenAuthHandler(identity_provider=TokenIdentityProvider())
    elif auth_strategy == "OAuth2Auth":
        return OAuth2AuthHandler(identity_provider=AzureIdentityProvider())
    else:
        raise ValueError(f"Unknown auth strategy: {auth_strategy}")
