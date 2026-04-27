import pytest


def mark_tests_by_directory(items: list[pytest.Item]) -> None:
    """Automatically assigns ``unit`` or ``integration`` markers based on the test file's directory."""
    for item in items:
        path = str(item.fspath)
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)


def attach_fixtures_to_items(
    items: list[pytest.Item],
    *fixture_names: str,
    path_substring: str | None = None,
) -> None:
    """Activates the named fixtures for every matching test item.

    The replacement for ``autouse=True``: activation becomes an explicit, opt-in
    declaration scoped by directory/path, never an implicit side effect of fixture
    definition. Modifies ``item.fixturenames`` directly so the fixtures are resolved
    during setup (adding a ``usefixtures`` marker post-collection has no effect — pytest's
    fixtureinfo is already computed before ``pytest_collection_modifyitems`` runs).

    Optional ``path_substring`` restricts attachment to items whose ``fspath`` contains it.
    """
    for item in items:
        if path_substring is not None and path_substring not in str(item.fspath):
            continue
        if not hasattr(item, "fixturenames"):
            continue
        # Insert at position 0 so attached fixtures set up before per-test fixtures —
        # matches the original ``autouse=True`` ordering (autouse runs first within scope).
        for name in reversed(fixture_names):
            if name not in item.fixturenames:
                item.fixturenames.insert(0, name)
