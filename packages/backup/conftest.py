import pytest

from swiss_ai_hub.core.testing.conftest_utils import mark_tests_by_directory


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    mark_tests_by_directory(items)
