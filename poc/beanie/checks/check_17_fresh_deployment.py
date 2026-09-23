"""Check 17 — does a fresh deployment have to replay migration history?

The EF Core question behind this: EF Core has an initial `InitialCreate`
migration, and a fresh database is bootstrapped by running migrations from #1.
`Database.Migrate()` at startup handles it. What is Beanie's equivalent?

Beanie has no initial migration, because MongoDB has no schema to create:
collections appear on first write and indexes come from `init_beanie`, not from a
migration. So a fresh deployment is usable with ZERO migrations run.

That creates the opposite problem, which this check measures. A fresh deployment
writes data in the CURRENT shape. Its `migrations_log` is empty, so the runner
believes NO migrations have been applied. Running `beanie migrate` therefore
applies historical migrations to data that is already in the post-migration
shape.

The CLI has no `--fake` / `--stamp` / baseline flag (verified against
`beanie migrate --help`), so there is no supported way to say "this database is
already current, just move the pointer".

Scenario: a migration that splits `full_name` into `first_name`/`last_name`
(the check 13 fixture). A fresh deployment writes first/last directly. What
happens when the historical migration runs against it?

    .venv/Scripts/python.exe poc/beanie/checks/check_17_fresh_deployment.py
"""

import asyncio
from pathlib import Path

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB = "aihub_beanie_spike"
COLLECTION = "migration_people"
MIGRATIONS_PATH = Path(__file__).parent / "migrations"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:200]}"


async def main() -> None:
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    db = client[SPIKE_DB]

    print("== 0. simulate a FRESH deployment ==")
    await db.drop_collection(COLLECTION)
    await db.drop_collection("migrations_log")
    # A fresh deployment's app writes the CURRENT shape -- first_name/last_name,
    # never full_name. It has no history to migrate.
    await db[COLLECTION].insert_many(
        [
            {"first_name": "Ada", "last_name": "Lovelace", "tenant": "t1"},
            {"first_name": "Alan", "last_name": "Turing", "tenant": "t1"},
        ]
    )
    rows = [row async for row in db[COLLECTION].find({}, sort=[("tenant", 1)])]
    for row in rows:
        print(f"    {({k: v for k, v in row.items() if k != '_id'})}")
    print(f"  migrations_log entries: {await db['migrations_log'].count_documents({})}  (empty -- nothing applied)")

    print("\n== 1. deploy runs `beanie migrate`, as it would on any environment ==")
    outcome: BaseException | None = None
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB,
                path=str(MIGRATIONS_PATH),
                direction="FORWARD",
                distance=0,
            )
        )
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        outcome = error
    print(f"  run_migrate -> {describe(outcome)}")

    print("\n== 2. what happened to the already-current data? ==")
    rows = [row async for row in db[COLLECTION].find({}, sort=[("tenant", 1)])]
    for row in rows:
        print(f"    {({k: v for k, v in row.items() if k != '_id'})}")
    logs = await db["migrations_log"].count_documents({})
    print(f"  migrations_log entries: {logs}")

    print("\n== 3. verdict ==")
    intact = all(row.get("first_name") in ("Ada", "Alan") for row in rows)
    if outcome is not None:
        print("  The migration RAISED against already-current data.")
        print("  -> a fresh deployment cannot simply run the full history; it needs baselining,")
        print("     and Beanie provides no --fake/--stamp flag to do it.")
    elif intact:
        print("  Data survived -- the migration was a no-op against the current shape.")
        print("  -> replaying history on a fresh deployment is safe FOR THIS migration,")
        print("     but that is a property of how it was written, not a guarantee.")
    else:
        print("  DATA CORRUPTED -- the historical migration rewrote already-current documents.")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
