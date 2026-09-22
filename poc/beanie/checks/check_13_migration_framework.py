"""Check 13 — does Beanie's migration framework actually work on FerretDB 2.5?

This is the check the earlier phases did not run, because the ADR answered the
question the ISSUE framed (two production performance symptoms) and this is a
different driver: issue #1152 wants versioned migrations that run automatically
on startup, `strict: True` once they exist, and a CI gate. Beanie ships a
migration framework; if it works here, #1634 and #1152 stop being independent
decisions.

What the framework does, read from the installed package rather than the docs:

  runner.py:167-176   always opens `client.start_session()`; wraps the run in
                      `s.start_transaction()` ONLY when use_transaction is set
  executors/migrate.py:58   use_transaction defaults to FALSE
  migrations/models.py      state is tracked in a `migrations_log` collection
                            as MigrationLog documents

So the decisive questions for FerretDB, in order of how fatal they are:

  1. does `start_session()` work at all?            -- fatal if not
  2. do writes accept `session=` outside a transaction? -- fatal if not
  3. does a forward migration transform documents?  -- fatal if not
  4. is the run recorded so it is not repeated?     -- fatal if not (no "auto" without it)
  5. does a backward migration roll back?           -- a cost, not fatal
  6. does `use_transaction=True` work?              -- a cost, not fatal, since it is off by default
"""

import asyncio
from pathlib import Path

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "migration_people"
MIGRATIONS_PATH = Path(__file__).parent / "migrations"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()

SEED = [
    {"full_name": "Ada Lovelace", "tenant": "t1"},
    {"full_name": "Alan Turing", "tenant": "t1"},
    {"full_name": "Grace", "tenant": "t2"},  # no surname -- the awkward row
]


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:200]}"


async def reset() -> AsyncMongoClient:
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    db = client[SPIKE_DB_NAME]
    await db.drop_collection(COLLECTION)
    await db.drop_collection("migrations_log")
    await db[COLLECTION].insert_many([dict(row) for row in SEED])
    return client


async def show(client: AsyncMongoClient, label: str) -> None:
    rows = [row async for row in client[SPIKE_DB_NAME][COLLECTION].find({}, sort=[("tenant", 1)])]
    print(f"  {label}")
    for row in rows:
        printable = {key: value for key, value in row.items() if key != "_id"}
        print(f"    {printable}")


async def show_log(client: AsyncMongoClient) -> None:
    rows = [row async for row in client[SPIKE_DB_NAME]["migrations_log"].find({})]
    if not rows:
        print("    migrations_log: EMPTY -- nothing recorded, so a re-run would repeat the migration")
        return
    for row in rows:
        print(f"    migrations_log: name={row.get('name')!r} is_current={row.get('is_current')} ts={row.get('ts')}")


async def main() -> None:
    print("== 1. can FerretDB open a session at all? ==")
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    outcome: BaseException | None = None
    try:
        async with client.start_session() as session:
            await client[SPIKE_DB_NAME]["session_probe"].insert_one({"x": 1}, session=session)
            found = await client[SPIKE_DB_NAME]["session_probe"].find_one({"x": 1}, session=session)
            print(f"  write+read inside a session: {'OK' if found else 'FAILED'}")
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        outcome = error
    print(f"  start_session() -> {describe(outcome)}")

    print("\n== 2. does FerretDB support start_transaction()? ==")
    outcome = None
    try:
        async with client.start_session() as session:
            async with await session.start_transaction():
                await client[SPIKE_DB_NAME]["session_probe"].insert_one({"x": 2}, session=session)
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"  start_transaction() -> {describe(outcome)}")
    await client[SPIKE_DB_NAME].drop_collection("session_probe")
    await client.close()

    print("\n== 3. forward migration, use_transaction=False (the default) ==")
    client = await reset()
    await show(client, "before:")
    outcome = None
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB_NAME,
                path=str(MIGRATIONS_PATH),
                direction="FORWARD",
                distance=0,
            )
        )
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"  run_migrate FORWARD -> {describe(outcome)}")
    await show(client, "after:")

    print("\n== 4. was the run recorded? (no 'auto' migration without this) ==")
    await show_log(client)

    print("\n== 5. is a second forward run a no-op? ==")
    outcome = None
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB_NAME,
                path=str(MIGRATIONS_PATH),
                direction="FORWARD",
                distance=0,
            )
        )
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"  second run -> {describe(outcome)}")
    await show(client, "after second run (must be unchanged):")

    print("\n== 6. backward migration (rollback) ==")
    outcome = None
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB_NAME,
                path=str(MIGRATIONS_PATH),
                direction="BACKWARD",
                distance=1,
            )
        )
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"  run_migrate BACKWARD -> {describe(outcome)}")
    await show(client, "after rollback:")

    print("\n== 7. forward migration WITH use_transaction=True ==")
    await client.close()
    client = await reset()
    outcome = None
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB_NAME,
                path=str(MIGRATIONS_PATH),
                direction="FORWARD",
                distance=0,
                use_transaction=True,
            )
        )
    except BaseException as error:  # noqa: BLE001
        outcome = error
    print(f"  run_migrate FORWARD (transactional) -> {describe(outcome)}")
    await show(client, "after:")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
