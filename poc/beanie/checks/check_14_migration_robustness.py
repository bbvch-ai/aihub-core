"""Check 14 — settle the three open questions the ADR leaves on automatic migrations.

Check 13 proved the framework works when called once, from a script, against one
database. The ADR's "Open questions" section names what that did not cover. Each
is answered here by an experiment rather than by reasoning:

  Q1 partial failure   A migration raises partway. FerretDB has no transactions,
                       so what does the collection look like afterwards, and what
                       does a retry do?
  Q2 concurrent boot   N API replicas start together and all call the runner.
                       Does `migrations_log` prevent a double-apply?
  Q3 many databases    Migrations across tenant databases, which is where check
                       05's routing finding would bite.

Q2 uses SEPARATE PROCESSES, not asyncio tasks. Beanie's DBHandler is module-global
state, so concurrent tasks in one process would contend on that rather than on the
database, and the result would be an artifact of the harness rather than a fact
about replicas.

    .venv/Scripts/python.exe poc/beanie/checks/check_14_migration_robustness.py
"""

import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB = "aihub_beanie_spike"
TENANT_DBS = ["aihub_beanie_spike_tenant_a", "aihub_beanie_spike_tenant_b"]

COUNTER_PATH = Path(__file__).parent / "migrations_counter"
FAILING_PATH = Path(__file__).parent / "migrations_failing"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:150]}"


def settings(path: Path, database: str) -> MigrationSettings:
    return MigrationSettings(
        connection_uri=CONNECTION_STRING,
        database_name=database,
        path=str(path),
        direction="FORWARD",
        distance=0,
    )


async def seed_counter(client: AsyncMongoClient, database: str) -> None:
    db = client[database]
    await db.drop_collection("migration_counter")
    await db.drop_collection("migrations_log")
    await db["migration_counter"].insert_many([{"key": f"row-{i}", "applied": 0} for i in range(3)])


async def counter_state(client: AsyncMongoClient, database: str) -> tuple[list[int], int]:
    db = client[database]
    applied = [row["applied"] async for row in db["migration_counter"].find({}, sort=[("key", 1)])]
    logs = await db["migrations_log"].count_documents({})
    return applied, logs


# ---------------------------------------------------------------------------- Q1


async def question_1_partial_failure() -> None:
    print("== Q1: what does a migration that fails partway leave behind? ==")
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    db = client[SPIKE_DB]
    await db.drop_collection("migration_partial")
    await db.drop_collection("migrations_log")
    await db["migration_partial"].insert_many(
        [
            {"key": "a-before", "state": "original"},
            {"key": "b-before", "state": "original"},
            {"key": "boom", "state": "original"},
            {"key": "z-after", "state": "original"},
        ]
    )

    outcome: BaseException | None = None
    try:
        await run_migrate(settings(FAILING_PATH, SPIKE_DB))
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        outcome = error
    print(f"  run_migrate -> {describe(outcome)}")

    rows = [row async for row in db["migration_partial"].find({}, sort=[("key", 1)])]
    for row in rows:
        print(f"    {row['key']:<10} state={row['state']!r}")
    migrated = sum(1 for row in rows if row["state"] == "migrated")
    logs = await db["migrations_log"].count_documents({})
    print(f"  {migrated}/{len(rows)} documents migrated, migrations_log entries: {logs}")
    if 0 < migrated < len(rows):
        print("  -> PARTIAL APPLICATION: the collection is in a mixed state with no record of it")
    elif migrated == 0:
        print("  -> nothing was written before the failure")
    await client.close()


# ---------------------------------------------------------------------------- Q2


async def worker() -> None:
    """One 'replica' calling the migration runner. Invoked as a separate process."""
    try:
        await run_migrate(settings(COUNTER_PATH, SPIKE_DB))
        print("worker: OK")
    except BaseException as error:  # noqa: BLE001
        print(f"worker: {type(error).__name__}: {str(error)[:120]}")


async def question_2_concurrent_boot(replicas: int) -> None:
    print(f"\n== Q2: {replicas} replicas call the runner at the same time ==")
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    await seed_counter(client, SPIKE_DB)
    before, _ = await counter_state(client, SPIKE_DB)
    print(f"  before: applied={before}")

    processes = [
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for _ in range(replicas)
    ]
    for index, process in enumerate(processes):
        output, _ = process.communicate(timeout=180)
        first_line = next((line for line in output.splitlines() if line.startswith("worker:")), "?")
        print(f"  replica {index}: {first_line}")

    after, logs = await counter_state(client, SPIKE_DB)
    print(f"  after : applied={after}, migrations_log entries={logs}")
    if any(value > 1 for value in after):
        print("  -> DOUBLE-APPLIED: migrations_log does not serialise concurrent runners")
    elif all(value == 1 for value in after):
        print("  -> applied exactly once despite concurrent runners")
    else:
        print("  -> inconsistent: some rows migrated, some not")
    await client.close()


# ---------------------------------------------------------------------------- Q3


async def question_3_many_databases() -> None:
    print("\n== Q3: migrations across several tenant databases ==")
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    for database in TENANT_DBS:
        await seed_counter(client, database)

    print("  -- sequentially, one database after another --")
    for database in TENANT_DBS:
        outcome: BaseException | None = None
        try:
            await run_migrate(settings(COUNTER_PATH, database))
        except BaseException as error:  # noqa: BLE001
            outcome = error
        applied, logs = await counter_state(client, database)
        print(f"    {database:<32} {describe(outcome):<12} applied={applied} log={logs}")

    print("  -- concurrently, in ONE process (the DBHandler global-state question) --")
    for database in TENANT_DBS:
        await seed_counter(client, database)
    results = await asyncio.gather(
        *[run_migrate(settings(COUNTER_PATH, database)) for database in TENANT_DBS],
        return_exceptions=True,
    )
    for database, result in zip(TENANT_DBS, results, strict=True):
        applied, logs = await counter_state(client, database)
        status = "OK" if not isinstance(result, BaseException) else type(result).__name__
        flag = "" if applied == [1, 1, 1] else "   <-- WRONG"
        print(f"    {database:<32} {status:<12} applied={applied} log={logs}{flag}")
    await client.close()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true", help="internal: act as one replica")
    parser.add_argument("--replicas", type=int, default=4)
    args = parser.parse_args()

    if args.worker:
        await worker()
        return

    await question_1_partial_failure()
    await question_2_concurrent_boot(args.replicas)
    await question_3_many_databases()


if __name__ == "__main__":
    asyncio.run(main())
