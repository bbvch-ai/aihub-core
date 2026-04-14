from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
    from swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
        DummyResponse,
        generate_rsa_keypair,
        public_key_to_jwk,
    )
    from swiss_ai_hub.core.testing.auth_utils.role_mocks import mock_role_entity_methods
    from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse
    from swiss_ai_hub.core.testing.auth_utils.user_mocks import (
        get_expected_user_data,
        mock_keycloak_admin_service_autouse,
    )
    from swiss_ai_hub.core.testing.route_adapter.asgi_adapter import ASGIAdapter

__all__ = [
    "async_test",
    "ASGIAdapter",
    "DummyResponse",
    "generate_rsa_keypair",
    "get_expected_user_data",
    "mock_role_entity_methods",
    "mock_tenant_entity_autouse",
    "mock_keycloak_admin_service_autouse",
    "public_key_to_jwk",
]

_LAZY_IMPORTS = {
    "async_test": "swiss_ai_hub.core.testing.asyncio_utils.bdd",
    "ASGIAdapter": "swiss_ai_hub.core.testing.route_adapter.asgi_adapter",
    "DummyResponse": "swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils",
    "generate_rsa_keypair": "swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils",
    "get_expected_user_data": "swiss_ai_hub.core.testing.auth_utils.user_mocks",
    "mock_role_entity_methods": "swiss_ai_hub.core.testing.auth_utils.role_mocks",
    "mock_tenant_entity_autouse": "swiss_ai_hub.core.testing.auth_utils.tenant_mocks",
    "mock_keycloak_admin_service_autouse": "swiss_ai_hub.core.testing.auth_utils.user_mocks",
    "public_key_to_jwk": "swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
