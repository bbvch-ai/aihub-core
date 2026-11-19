import pytest
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# MUST be the first ``swiss_ai_hub`` import — sets AIHUB_MONGO_MAIN_DB_NAME=aihub_test
# at import time so subsequent ``AIHubSettings()`` instantiations resolve to the test DB.
from swiss_ai_hub.core.testing.db_isolation import isolate_test_db  # noqa: E402, F401

# isort: split
from swiss_ai_hub.core.testing.conftest_utils import attach_fixtures_to_items  # noqa: E402


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Activates the test-DB isolation fixture for every collected test."""
    attach_fixtures_to_items(items, "isolate_test_db")


@pytest.fixture(autouse=True)
def in_memory_parse_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    """Attached files keep their sections and embeddings in the parse-cache bucket; a test keeps them in memory, one
    store per test, so no test reaches S3 or sees another's entries."""
    from swiss_ai_hub.core.generative_ai import ParseCacheBucket

    store: dict[str, bytes] = {}
    monkeypatch.setattr(ParseCacheBucket, "read", lambda _self, key: store.get(key))
    monkeypatch.setattr(
        ParseCacheBucket, "write", lambda _self, key, content, _content_type: store.update({key: content})
    )
    return store
