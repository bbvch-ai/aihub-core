"""Check 14b — does the partial-failure guarantee hold for a free-fall migration?

Check 14 Q1 found that an `@iterative_migration` which fails partway writes
NOTHING: Beanie collects its `replace_many` calls as coroutines and awaits none of
them until the whole collection is transformed (iterative.py:93-128). That makes
"refuse to start on migration failure" a safe policy for that kind.

`@free_fall_migration` is built differently. `free_fall.py` is four lines long and
simply awaits the author's function:

    async def run(self, session):
        function_kwargs = {"session": session}
        if "self" in self.function_signature.parameters:
            function_kwargs["self"] = None
        await self.function(**function_kwargs)

Nothing is collected and nothing is deferred, so whatever the function writes lands
as it goes. This check measures what that means when it fails partway -- it is the
evidence behind rule 6 and behind the Rollback section's claim that a failed
free-fall migration needs a forward re-run rather than a backward one.

Free-fall cannot simply be banned: it is the only kind that can create an index,
touch two collections, or rename a field with `$rename`.

    .venv/Scripts/python.exe poc/beanie/checks/check_14b_freefall_partial_failure.py
"""

import asyncio
from pathlib import Path

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB = "aihub_beanie_spike"
COLLECTION = "freefall_partial"
MIGRATIONS_PATH = Path(__file__).parent / "migrations_freefall"

CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()

# Ordered so that two documents are processed before the one that raises, and one after.
SEED = [
    {"key": "a-before", "state": "original"},
    {"key": "b-before", "state": "original"},
    {"key": "boom", "state": "original"},
    {"key": "z-after", "state": "original"},
]


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:160]}"


async def main() -> None:
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    db = client[SPIKE_DB]

    print("== 0. clean slate ==")
    await db.drop_collection(COLLECTION)
    await db.drop_collection("migrations_log")
    await db[COLLECTION].insert_many([dict(row) for row in SEED])
    print(f"seeded {len(SEED)} documents, all state='original'")

    print("\n== 1. run the free-fall migration that raises on the third document ==")
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

    print("\n== 2. what did it leave behind? ==")
    rows = [row async for row in db[COLLECTION].find({}, sort=[("key", 1)])]
    for row in rows:
        print(f"    {row['key']:<10} state={row['state']!r}")
    migrated = sum(1 for row in rows if row["state"] == "migrated")
    logs = await db["migrations_log"].count_documents({})
    print(f"  {migrated}/{len(rows)} documents migrated, migrations_log entries: {logs}")

    print("\n== 3. verdict ==")
    if 0 < migrated < len(rows):
        print("  PARTIAL APPLICATION -- the collection is in a mixed state.")
        print("  Contrast check 14 Q1, where the same failure as an iterative migration wrote 0/4.")
        if logs == 0:
            print("  And migrations_log is EMPTY, so nothing records that a partial write happened.")
            print("  -> a backward run would undo the PREVIOUS migration, not this one (see check 15 T2)")
            print("  -> recovery is a forward RE-RUN, which is only safe if the migration is idempotent (rule 6)")
    elif migrated == 0:
        print("  Nothing was written -- free-fall would share the iterative guarantee after all.")
    else:
        print("  Everything was written despite the failure -- investigate before trusting this result.")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
