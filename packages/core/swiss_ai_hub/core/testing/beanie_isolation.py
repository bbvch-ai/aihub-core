"""Shared-loop test setup for Beanie documents, the entities ported from MongoEngine (#1634).

A Beanie document is bound to an ``AsyncMongoClient``, and that client works only on the event loop it was
created on. pytest-asyncio gives every async test its own loop, so the client is created once on pytest-asyncio's
session loop, and only tests marked ``beanie`` run on that loop. Every other test keeps its own loop, which is why
the opt-in is per test or per module rather than a suite-wide loop scope.

Each package that opts tests in imports both fixtures and ``mark_beanie_test_for_session_loop`` into its top-level
``conftest.py``, calls the latter from a ``pytest_pycollect_makeitem`` hook, registers the ``beanie`` marker, and
defines a session-scoped ``beanie_document_models`` fixture listing the documents to initialise.
"""

import inspect
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

BEANIE_MARKER = "beanie"


def mark_beanie_test_for_session_loop(collector: pytest.Collector, name: str, obj: object) -> None:
    """Moves an async test marked ``beanie`` onto the session loop and gives it a clean database.

    Runs during collection, before pytest-asyncio turns the function into a test item: pytest-asyncio reads the
    ``asyncio`` mark at that point, so adding it later in ``pytest_collection_modifyitems`` is too late.
    """
    # pytest offers every module attribute here; an imported async helper must not be marked in its own module
    if not name.startswith("test") or not inspect.iscoroutinefunction(obj):
        return
    marked_itself = any(mark.name == BEANIE_MARKER for mark in getattr(obj, "pytestmark", []))
    if not marked_itself and collector.get_closest_marker(BEANIE_MARKER) is None:
        return
    pytest.mark.asyncio(loop_scope="session")(obj)
    pytest.mark.usefixtures("clean_beanie_collections")(obj)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def beanie_test_database(
    isolate_test_db: None,
    beanie_document_models: list[type[Document]],
) -> AsyncGenerator[AsyncDatabase]:
    """Initialises the package's Beanie documents once, after ``isolate_test_db`` has dropped the test database."""
    client: AsyncMongoClient = AsyncMongoClient(
        MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    database = client[AIHubSettings().MONGO_MAIN_DB_NAME]
    await init_beanie(database=database, document_models=beanie_document_models)
    yield database
    await client.close()


@pytest_asyncio.fixture(loop_scope="session")
async def clean_beanie_collections(
    beanie_test_database: AsyncDatabase,
    beanie_document_models: list[type[Document]],
) -> None:
    """Empties every initialised collection before the test, so no test sees another's data.

    Deletes documents rather than dropping collections, which would also drop the indexes ``init_beanie`` created.
    """
    for document_model in beanie_document_models:
        await document_model.delete_all()
