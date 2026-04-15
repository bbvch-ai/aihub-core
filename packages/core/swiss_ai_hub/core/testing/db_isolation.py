"""Test-DB isolation: forces every test session to use a dedicated MongoDB
database so tests never read or write the dev/prod ``aihub`` database.

Each package's top-level ``conftest.py`` MUST import this module **before** any
``swiss_ai_hub.*`` import, because the env override happens at import time and
must run before any code constructs ``AIHubSettings()`` or calls
``mongoengine.connect(...)``. Once the env var is set, every existing
``AIHubSettings().MONGO_MAIN_DB_NAME`` reference resolves to ``aihub_test``.

The autouse session fixture additionally drops the test database at session
start so stale rows from a prior session (e.g. ``BearerToken`` static-token
rows that conflict on the unique ``token`` index) cannot leak across runs. The
drop tolerates MongoDB being unreachable — packages whose tests do not touch
Mongo still benefit from the env override but will not fail at startup.
"""

import os
from collections.abc import Generator

# Override at import time. Must precede any ``swiss_ai_hub.*`` import below.
TEST_DB_NAME = "aihub_test"
os.environ["AIHUB_MONGO_MAIN_DB_NAME"] = TEST_DB_NAME

import pytest  # noqa: E402
from pymongo import MongoClient  # noqa: E402

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings  # noqa: E402
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _isolate_test_db() -> Generator[None]:
    db_name = AIHubSettings().MONGO_MAIN_DB_NAME
    assert db_name == TEST_DB_NAME, (
        f"Test isolation broken: AIHUB_MONGO_MAIN_DB_NAME resolved to '{db_name}', "
        f"expected '{TEST_DB_NAME}'. The conftest must import "
        "``swiss_ai_hub.core.testing.db_isolation`` before any other ``swiss_ai_hub`` import."
    )
    try:
        client = MongoClient(
            MongoSettings().CONNECTION_STRING.get_secret_value(),
            serverSelectionTimeoutMS=2000,
        )
        client.admin.command("ping")
        client.drop_database(db_name)
        client.close()
    except Exception:
        pass
    yield
