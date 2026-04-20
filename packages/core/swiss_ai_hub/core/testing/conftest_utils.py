import pytest


def mark_tests_by_directory(items: list[pytest.Item]) -> None:
    """Automatically assigns ``unit`` or ``integration`` markers based on the test file's directory."""
    for item in items:
        path = str(item.fspath)
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
