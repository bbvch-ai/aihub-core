from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
    from swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
        DummyResponse,
        generate_rsa_keypair,
        public_key_to_jwk,
    )
    from swiss_ai_hub.core.testing.auth_utils.role_mocks import mock_role_entity_methods
    from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity
    from swiss_ai_hub.core.testing.auth_utils.user_mocks import (
        get_expected_user_data,
        mock_keycloak_admin_service,
    )
    from swiss_ai_hub.core.testing.conftest_utils import attach_fixtures_to_items, mark_tests_by_directory
    from swiss_ai_hub.core.testing.db_isolation import isolate_test_db
    from swiss_ai_hub.core.testing.route_adapter.asgi_adapter import ASGIAdapter

__all__ = [
    "async_test",
    "ASGIAdapter",
    "attach_fixtures_to_items",
    "isolate_test_db",
    "mark_tests_by_directory",
    "DummyResponse",
    "generate_rsa_keypair",
    "get_expected_user_data",
    "mock_role_entity_methods",
    "mock_tenant_entity",
    "mock_keycloak_admin_service",
    "public_key_to_jwk",
]

_OAUTH2_TEST_UTILS_MODULE = "swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils"

_LAZY_IMPORTS = {
    "async_test": "swiss_ai_hub.core.testing.asyncio_utils.bdd",
    "attach_fixtures_to_items": "swiss_ai_hub.core.testing.conftest_utils",
    "isolate_test_db": "swiss_ai_hub.core.testing.db_isolation",
    "mark_tests_by_directory": "swiss_ai_hub.core.testing.conftest_utils",
    "ASGIAdapter": "swiss_ai_hub.core.testing.route_adapter.asgi_adapter",
    "DummyResponse": _OAUTH2_TEST_UTILS_MODULE,
    "generate_rsa_keypair": _OAUTH2_TEST_UTILS_MODULE,
    "get_expected_user_data": "swiss_ai_hub.core.testing.auth_utils.user_mocks",
    "mock_role_entity_methods": "swiss_ai_hub.core.testing.auth_utils.role_mocks",
    "mock_tenant_entity": "swiss_ai_hub.core.testing.auth_utils.tenant_mocks",
    "mock_keycloak_admin_service": "swiss_ai_hub.core.testing.auth_utils.user_mocks",
    "public_key_to_jwk": _OAUTH2_TEST_UTILS_MODULE,
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
