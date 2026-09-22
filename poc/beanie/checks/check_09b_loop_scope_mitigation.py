"""Check 09b — does widening pytest-asyncio's loop scope rescue a shared Beanie client?

check_09 showed that a module-scoped `AsyncMongoClient` breaks under the default
per-test loop. pytest-asyncio 1.3 can widen the loop scope, so a session-scoped
loop with a session-scoped client is the obvious mitigation. Testing it here so
the cost recorded against Beanie is the cost that actually remains, not the cost
before the fix anyone would reach for.

    .venv/Scripts/python.exe -m pytest poc/beanie/checks/check_09b_loop_scope_mitigation.py -v -s

Note what widening the loop scope means for the suite as a whole: tests stop
getting a clean loop each, so state leaks between them by design. That is a
trade, not a free win, and it applies to all 913 `@pytest.mark.asyncio` tests --
not only the ones touching Mongo.
"""

import asyncio
from typing import Any

import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "loop_scope"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()


class ScopedProbe(Document):
    key: str

    class Settings:
        name = COLLECTION


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:140]}"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def session_beanie() -> Any:
    """Initialised once, inside the session-scoped loop that the tests below also run in."""
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    await init_beanie(database=client[SPIKE_DB_NAME], document_models=[ScopedProbe])
    yield client
    await client.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_first_test_on_the_session_loop(session_beanie: Any) -> None:
    outcome: BaseException | None = None
    try:
        await ScopedProbe(key="session-loop-1").insert()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"\n[E1] session-scoped loop + session-scoped client, test 1 -> {describe(outcome)}")
    print(f"     loop id: {id(asyncio.get_running_loop())}")


@pytest.mark.asyncio(loop_scope="session")
async def test_second_test_on_the_session_loop(session_beanie: Any) -> None:
    outcome: BaseException | None = None
    try:
        await ScopedProbe(key="session-loop-2").insert()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"[E2] session-scoped loop + session-scoped client, test 2 -> {describe(outcome)}")
    print(f"     loop id: {id(asyncio.get_running_loop())}  (same id as E1 = one shared loop)")


@pytest.mark.asyncio
async def test_a_default_scoped_test_alongside_them(session_beanie: Any) -> None:
    """A test left on the DEFAULT per-test loop, using the session client. The mixed case."""
    outcome: BaseException | None = None
    try:
        await ScopedProbe(key="default-loop").insert()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"[E3] DEFAULT per-test loop + session-scoped client -> {describe(outcome)}")
    print(f"     loop id: {id(asyncio.get_running_loop())}  (different id = the mismatch)")


def test_asyncio_run_alongside_a_session_loop() -> None:
    """The @async_test pattern cannot join a session loop: asyncio.run() always makes its own."""
    outcome: BaseException | None = None
    try:
        asyncio.run(ScopedProbe(key="asyncio-run").insert())
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"[E4] asyncio.run() (the @async_test shape) against the session client -> {describe(outcome)}")
