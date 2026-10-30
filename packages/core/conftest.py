import pytest
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# Must be the first ``swiss_ai_hub`` import — sets ``AIHUB_MONGO_MAIN_DB_NAME=aihub_test`` at
# import time so anything that later constructs ``AIHubSettings`` picks up the test DB name.
# The ``# isort: split`` marker below stops ruff/isort from merging this with the block that
# follows and re-alphabetising the lines, which would move this import below the auth mocks.
from swiss_ai_hub.core.testing.db_isolation import isolate_test_db  # noqa: E402, F401

# isort: split
from beanie import Document  # noqa: E402

from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service  # noqa: E402, F401
from swiss_ai_hub.core.testing.beanie_isolation import (  # noqa: E402, F401
    beanie_test_database,
    clean_beanie_collections,
    mark_beanie_test_for_session_loop,
)
from swiss_ai_hub.core.testing.conftest_utils import attach_fixtures_to_items, mark_tests_by_directory  # noqa: E402
from swiss_ai_hub.core.testing.tests.unit.beanie_probe_document import BeanieProbeDocument  # noqa: E402


@pytest.fixture(scope="session")
def beanie_document_models() -> list[type[Document]]:
    """The Beanie documents ``beanie`` tests in this package run against."""
    return [BeanieProbeDocument]


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_pycollect_makeitem(collector: pytest.Collector, name: str, obj: object) -> object:
    mark_beanie_test_for_session_loop(collector, name, obj)
    return (yield)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marks tests by directory and activates the fake Keycloak admin for unit tests only.

    Scopes the fake by directory so integration tests remain untouched and can hit the real
    Keycloak without per-test monkeypatch counter-overrides.
    """
    mark_tests_by_directory(items)
    attach_fixtures_to_items(items, "isolate_test_db")
    attach_fixtures_to_items(items, "mock_keycloak_admin_service", path_substring="/tests/unit/")
