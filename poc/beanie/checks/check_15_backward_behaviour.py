"""Check 15 — what does a backward run actually do?

Check 13 ran one backward migration and it reverted correctly. That is the happy
path. This check probes the three behaviours the Rollback section depends on, each
of which is SILENT in Beanie's source:

  T1  A migration with no `Backward` class. `runner.py:133-144`:

          async def run_backward(self, allow_index_dropping, use_transaction):
              if self.backward_class is not None:        # <- optional
                  await self.run_migration_class(...)
              if self.prev_migration is not None:        # <- runs REGARDLESS
                  await self.prev_migration.update_current_migration()

      The body is skipped and the log pointer moves anyway. Does the run report
      success while the data stays migrated?  -> rule 7

  T2  A migration that failed partway never reached `migrations_log`, so the
      runner's idea of "the last migration" is the previous, healthy one. Does
      `--direction BACKWARD --distance 1` therefore undo the WRONG migration?
      -> the Rollback section's "a failed migration is not recovered by a
      backward run"

  T3  `distance=0` logs "Running migrations backward without limit"
      (`runner.py:102`) and is the CLI default (`executors/migrate.py:31-34`).
      Does a bare backward run undo EVERY migration ever applied?  -> rule 8

Each uses its own migrations directory so the scenarios cannot contaminate each
other, and its own collection so the state is unambiguous.

    .venv/Scripts/python.exe poc/beanie/checks/check_15_backward_behaviour.py
"""

import asyncio
from pathlib import Path
from typing import Any

from beanie.executors.migrate import MigrationSettings, run_migrate
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB = "aihub_beanie_spike"
CONNECTION_STRING = MongoSettings().CONNECTION_STRING.get_secret_value()

HERE = Path(__file__).parent
T1_PATH = HERE / "migrations_no_backward"
T2_PATH = HERE / "migrations_healthy_then_failing"
T3_PATH = HERE / "migrations_chain"


def describe(outcome: BaseException | None) -> str:
    return "OK" if outcome is None else f"{type(outcome).__name__}: {str(outcome)[:150]}"


async def migrate(path: Path, direction: str, distance: int) -> BaseException | None:
    try:
        await run_migrate(
            MigrationSettings(
                connection_uri=CONNECTION_STRING,
                database_name=SPIKE_DB,
                path=str(path),
                direction=direction,
                distance=distance,
            )
        )
        return None
    except BaseException as error:  # noqa: BLE001 - the exception IS the finding
        return error


async def state(client: AsyncMongoClient, collection: str) -> tuple[list[Any], list[str]]:
    db = client[SPIKE_DB]
    rows = [row async for row in db[collection].find({}, sort=[("key", 1)])]
    values = [row.get("state", row.get("applied")) for row in rows]
    log = [row["name"] async for row in db["migrations_log"].find({})]
    return values, log


async def reset(client: AsyncMongoClient, collection: str, seed: list[dict[str, Any]]) -> None:
    db = client[SPIKE_DB]
    await db.drop_collection(collection)
    await db.drop_collection("migrations_log")
    await db[collection].insert_many([dict(row) for row in seed])


async def t1_no_backward(client: AsyncMongoClient) -> None:
    print("== T1: a migration that declares no Backward class ==")
    collection = "backward_t1"
    await reset(client, collection, [{"key": f"row-{i}", "state": "original"} for i in range(3)])

    print(f"  forward  -> {describe(await migrate(T1_PATH, 'FORWARD', 0))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}")

    print(f"  backward -> {describe(await migrate(T1_PATH, 'BACKWARD', 1))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}")

    if all(v == "migrated" for v in values):
        print("  -> DATA STILL MIGRATED after a backward run that did not raise.")
        print("     The pointer moved; the data did not. Silent. Source of rule 7.")
    else:
        print("  -> data reverted; Beanie must require or synthesise a Backward after all.")


async def t2_failed_then_backward(client: AsyncMongoClient) -> None:
    print("\n== T2: migration A healthy, migration B fails partway, then backward distance 1 ==")
    collection = "backward_t2"
    await reset(client, collection, [{"key": f"row-{i}", "state": "original"} for i in range(3)])

    print(f"  forward (A then B, B raises) -> {describe(await migrate(T2_PATH, 'FORWARD', 0))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}")
    print("    (B is absent from the log -- it never completed)")

    print(f"  backward distance 1 -> {describe(await migrate(T2_PATH, 'BACKWARD', 1))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}")
    print("  -> if the data is now PRE-A, the backward run undid the healthy migration,")
    print("     not the failed one. Recovery from a failed migration is a forward re-run.")


async def t3_default_distance(client: AsyncMongoClient) -> None:
    print("\n== T3: a bare backward run, distance left at its default of 0 ==")
    collection = "backward_t3"
    await reset(client, collection, [{"key": f"row-{i}", "applied": 0} for i in range(3)])

    print(f"  forward all three -> {describe(await migrate(T3_PATH, 'FORWARD', 0))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}  (expect 3 applications)")

    print(f"  backward, distance=0 (the CLI default) -> {describe(await migrate(T3_PATH, 'BACKWARD', 0))}")
    values, log = await state(client, collection)
    print(f"    data={values}  log={log}")
    if all(v == 0 for v in values):
        print("  -> ALL THREE migrations were undone by a run that named no distance.")
        print("     distance=0 means 'without limit', not 'one step'. Source of rule 8.")
    else:
        print("  -> only some were undone; re-read runner.py:99-118 before trusting rule 8.")


async def main() -> None:
    client: AsyncMongoClient = AsyncMongoClient(CONNECTION_STRING)
    await t1_no_backward(client)
    await t2_failed_then_backward(client)
    await t3_default_distance(client)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
