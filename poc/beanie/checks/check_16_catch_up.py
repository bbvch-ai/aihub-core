"""Check 16 — can an environment several migrations behind catch up in one command?

The EF Core question: an environment is 6-8 migrations behind, and
`dotnet ef database update` brings it current in one go. Does `beanie migrate`
do the same?

Reading `runner.py:75-97`, it should: a FORWARD run with `distance=0` logs
"Running migrations forward without limit" and walks `next_migration` until the
list is exhausted, starting from wherever `migrations_log`'s `is_current` pointer
sits. But "should" is not "does", and the interesting case is not a fresh
database -- it is resuming from the MIDDLE, which is where a wrong pointer would
show up as either a skipped migration or a re-applied one.

Three scenarios, using a chain of three counter migrations (each increments
`applied` by 1, so the value is an unambiguous record of how many ran):

  S1  fresh database, bare `migrate`            -> expect applied=3
  S2  one migration applied, then bare `migrate` -> expect applied=3, NOT 4
                                                    (migration 1 must not re-run)
  S3  all applied, then a fourth arrives         -> expect applied=4
                                                    (only the new one runs)

S2 is the EF Core question. S3 is the ordinary deploy case.

    .venv/Scripts/python.exe poc/beanie/checks/check_16_catch_up.py
"""

import asyncio
import shutil
from pathlib import Path

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB = "aihub_beanie_spike"
COLLECTION = "backward_t3"  # the chain migrations target this collection
CHAIN = Path(__file__).parent / "migrations_chain"
STAGING = Path(__file__).parent / "migrations_catchup_tmp"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:140]}"


def stage(count: int) -> None:
    """Expose only the first `count` migrations of the chain, simulating a release."""
    if STAGING.exists():
        shutil.rmtree(STAGING)
    STAGING.mkdir()
    for step in sorted(CHAIN.glob("*.py"))[:count]:
        shutil.copy(step, STAGING / step.name)


async def migrate(distance: int) -> BaseException | None:
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB,
                path=str(STAGING),
                direction="FORWARD",
                distance=distance,
            )
        )
        return None
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        return error


async def snapshot(client: AsyncMongoClient) -> tuple[list[int], str | None, int]:
    db = client[SPIKE_DB]
    applied = [row["applied"] async for row in db[COLLECTION].find({}, sort=[("key", 1)])]
    current = await db["migrations_log"].find_one({"is_current": True})
    total = await db["migrations_log"].count_documents({})
    return applied, (current or {}).get("name"), total


async def reset(client: AsyncMongoClient) -> None:
    db = client[SPIKE_DB]
    await db.drop_collection(COLLECTION)
    await db.drop_collection("migrations_log")
    await db[COLLECTION].insert_many([{"key": f"row-{i}", "applied": 0} for i in range(3)])


async def main() -> None:
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    available = len(sorted(CHAIN.glob("*.py")))
    print(f"chain has {available} migrations, each incrementing `applied` by 1\n")

    # ---------------------------------------------------------------- S1
    print("== S1: fresh database, bare `migrate` (distance defaults to 0) ==")
    await reset(client)
    stage(3)
    print(f"  migrate -> {describe(await migrate(0))}")
    applied, current, total = await snapshot(client)
    print(f"    applied={applied}  current={current}  log_entries={total}")
    print(f"    {'PASS' if applied == [3, 3, 3] else 'UNEXPECTED'}: all three ran\n")

    # ---------------------------------------------------------------- S2
    print("== S2: THE EF CORE CASE -- one applied, then bare `migrate` ==")
    await reset(client)
    stage(3)
    print(f"  migrate --distance 1 (simulating an environment left behind) -> {describe(await migrate(1))}")
    applied, current, total = await snapshot(client)
    print(f"    applied={applied}  current={current}")
    print("  now bring it current with a bare `migrate`:")
    print(f"  migrate -> {describe(await migrate(0))}")
    applied, current, total = await snapshot(client)
    print(f"    applied={applied}  current={current}  log_entries={total}")
    if applied == [3, 3, 3]:
        print("    PASS: caught up to 3. Migration 1 did NOT re-run -- it would read 4.\n")
    elif applied == [4, 4, 4]:
        print("    FAIL: 4 means migration 1 was applied twice.\n")
    else:
        print(f"    UNEXPECTED: {applied}\n")

    # ---------------------------------------------------------------- S3
    print("== S3: all applied, then a new migration arrives in the next release ==")
    await reset(client)
    stage(2)
    print(f"  release N   (2 migrations) -> {describe(await migrate(0))}")
    applied, current, _ = await snapshot(client)
    print(f"    applied={applied}  current={current}")
    stage(3)
    print(f"  release N+1 (3 migrations) -> {describe(await migrate(0))}")
    applied, current, total = await snapshot(client)
    print(f"    applied={applied}  current={current}  log_entries={total}")
    if applied == [3, 3, 3]:
        print("    PASS: only the new migration ran.\n")
    else:
        print(f"    UNEXPECTED: {applied}\n")

    if STAGING.exists():
        shutil.rmtree(STAGING)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
