"""Check 09 — does Beanie survive this repo's test infrastructure?

Run with pytest, because the loop lifecycle is the thing under test and only the
real runner reproduces it:

    .venv/Scripts/python.exe -m pytest poc/beanie/checks/check_09_test_infrastructure.py -v -s

Three patterns exist in the suite and each treats the event loop differently:

  @async_test          183 uses. Wraps each step in `asyncio.run()`, so a BDD
                       scenario spanning N steps creates and destroys N loops.
                       (core/testing/asyncio_utils/bdd.py:11)
  @pytest.mark.asyncio 913 uses. No `asyncio_mode` is configured anywhere, so
                       pytest-asyncio runs strict with a per-test loop.
  db_isolation         Session-autouse fixture using a SYNC MongoClient to drop
                       the test DB. Should be indifferent to Beanie -- verify.

`AsyncMongoClient` is loop-bound and `init_beanie` stores the client on the
Document class (process-wide, as check 05 established the hard way). So a client
initialised under one loop is still attached to the class when the next loop
starts. These tests find out what that actually does.
"""

import asyncio
import time
from typing import Any

import pytest
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient, MongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "test_infrastructure"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()


class Probe(Document):
    key: str
    value: int

    class Settings:
        name = COLLECTION


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:160]}"


# --------------------------------------------------------------------------------------
# A. the @async_test pattern: one asyncio.run() per step
# --------------------------------------------------------------------------------------


def test_a_client_initialised_in_one_asyncio_run_used_in_the_next() -> None:
    """A BDD scenario's step 2 inherits the class-level client that step 1 created."""
    holder: dict[str, Any] = {}

    async def step_one() -> None:
        client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
        holder["client"] = client
        await init_beanie(database=client[SPIKE_DB_NAME], document_models=[Probe])
        await Probe(key="from-step-one", value=1).insert()

    async def step_two() -> None:
        # No re-init: exactly what a second @async_test step would do.
        await Probe.find_one(Probe.key == "from-step-one")

    asyncio.run(step_one())  # loop 1 is created, used and CLOSED here

    outcome: BaseException | None = None
    try:
        asyncio.run(step_two())  # loop 2
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        outcome = error

    print(f"\n[A] reuse across asyncio.run() boundaries -> {describe(outcome)}")
    holder["outcome"] = outcome


def test_a2_reinitialising_in_each_asyncio_run_is_the_workaround() -> None:
    """If A fails, does re-initialising per step recover it, and what does it cost?"""

    async def step(index: int) -> float:
        started = time.perf_counter()
        client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
        await init_beanie(database=client[SPIKE_DB_NAME], document_models=[Probe])
        await Probe(key=f"reinit-{index}", value=index).insert()
        await client.close()
        return time.perf_counter() - started

    outcome: BaseException | None = None
    durations: list[float] = []
    try:
        for index in range(5):
            durations.append(asyncio.run(step(index)))
    except BaseException as error:  # noqa: BLE001
        outcome = error

    average = sum(durations) / len(durations) if durations else 0.0
    print(f"[A2] re-init inside every asyncio.run() -> {describe(outcome)}; "
          f"{len(durations)} steps, {average * 1000:.0f} ms each")


# --------------------------------------------------------------------------------------
# B. the @pytest.mark.asyncio pattern: a fresh loop per test, shared fixture across them
# --------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def module_scoped_beanie() -> Any:
    """The natural fixture shape: connect once for the module, like conftest does for Mongo."""
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    asyncio.run(init_beanie(database=client[SPIKE_DB_NAME], document_models=[Probe]))
    return client


@pytest.mark.asyncio
async def test_b1_first_test_using_a_module_scoped_client(module_scoped_beanie: Any) -> None:
    outcome: BaseException | None = None
    try:
        await Probe(key="module-scoped-1", value=1).insert()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"\n[B1] first test, module-scoped client -> {describe(outcome)}")


@pytest.mark.asyncio
async def test_b2_second_test_using_the_same_module_scoped_client(module_scoped_beanie: Any) -> None:
    """pytest-asyncio gives this test a DIFFERENT loop from B1's."""
    outcome: BaseException | None = None
    try:
        await Probe(key="module-scoped-2", value=2).insert()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"[B2] second test, SAME module-scoped client, new loop -> {describe(outcome)}")


@pytest.mark.asyncio
async def test_b3_function_scoped_init_is_the_workaround() -> None:
    """Re-initialising inside each test, which is what a function-scoped fixture would do."""
    started = time.perf_counter()
    outcome: BaseException | None = None
    try:
        client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
        await init_beanie(database=client[SPIKE_DB_NAME], document_models=[Probe])
        await Probe(key="function-scoped", value=3).insert()
        await client.close()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"[B3] per-test init -> {describe(outcome)}; {(time.perf_counter() - started) * 1000:.0f} ms")


# --------------------------------------------------------------------------------------
# C. db_isolation
# --------------------------------------------------------------------------------------


def test_c_db_isolation_uses_a_sync_client_and_is_unaffected() -> None:
    """The session fixture drops the test DB with a SYNC MongoClient. Beanie should not change that."""
    outcome: BaseException | None = None
    try:
        client: MongoClient = MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.drop_database("aihub_beanie_spike_isolation_probe")
        client.close()
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"\n[C] sync drop_database (the db_isolation mechanism) -> {describe(outcome)}")


# --------------------------------------------------------------------------------------
# D. the stale-class hazard: does a dead loop's client linger on the Document class?
# --------------------------------------------------------------------------------------


def test_d_document_class_retains_the_client_after_its_loop_dies() -> None:
    """init_beanie mutates class state. Check whether a closed loop's client is still attached."""

    async def initialise() -> None:
        client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
        await init_beanie(database=client[SPIKE_DB_NAME], document_models=[Probe])

    asyncio.run(initialise())

    settings = getattr(Probe, "_document_settings", None)
    collection = getattr(settings, "motor_collection", None) or getattr(settings, "pymongo_collection", None)
    print(f"\n[D] Document class still holds a collection handle after its loop closed: {collection is not None}")
    if collection is not None:
        print(f"    handle: {type(collection).__name__}")
