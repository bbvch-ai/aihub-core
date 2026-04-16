import pytest
from dotenv import find_dotenv, load_dotenv

from swiss_ai_hub.core.testing.conftest_utils import mark_tests_by_directory

load_dotenv(find_dotenv(usecwd=True))


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    mark_tests_by_directory(items)
