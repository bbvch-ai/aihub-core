import pytest
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# Must be the first ``swiss_ai_hub`` import — sets ``AIHUB_MONGO_MAIN_DB_NAME=aihub_test`` at
# import time so anything that later constructs ``AIHubSettings`` picks up the test DB name.
# The ``# isort: split`` marker below stops ruff/isort from merging this with the block that
# follows and re-alphabetising the lines, which would move this import below the auth mocks.
from swiss_ai_hub.core.testing.db_isolation import _isolate_test_db  # noqa: E402, F401

# isort: split
from swiss_ai_hub.core.testing.conftest_utils import mark_tests_by_directory  # noqa: E402


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    mark_tests_by_directory(items)
