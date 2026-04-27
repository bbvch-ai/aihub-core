import pytest
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# MUST be the first ``swiss_ai_hub`` import — sets AIHUB_MONGO_MAIN_DB_NAME=aihub_test
# at import time so subsequent ``AIHubSettings()`` instantiations resolve to the test DB.
from swiss_ai_hub.core.testing.db_isolation import isolate_test_db  # noqa: E402, F401

# isort: split
from swiss_ai_hub.core.testing.conftest_utils import attach_fixtures_to_items, mark_tests_by_directory  # noqa: E402


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Marks tests by directory and activates the test-DB isolation fixture for every test."""
    mark_tests_by_directory(items)
    attach_fixtures_to_items(items, "isolate_test_db")
