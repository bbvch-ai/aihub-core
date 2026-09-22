"""Check 08 — can a sync MongoClient and an AsyncMongoClient share a collection?

This decides the migration SHAPE, not whether Beanie works. If the two cannot
coexist in one process, incremental migration is off the table and only big-bang
across 35 document classes and 139 call sites remains.

It also probes the thing the migration is meant to fix: during coexistence the
un-migrated half still blocks the event loop. That is measured here rather than
asserted.
"""

import asyncio
import time
from typing import Any

from beanie import Document, init_beanie
from mongoengine import Document as MEDocument, IntField, StringField, connect, disconnect
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "coexistence"


class BeanieSide(Document):
    key: str
    value: int
    written_by: str

    class Settings:
        name = COLLECTION


class MongoEngineSide(MEDocument):
    meta = {"collection": COLLECTION, "strict": False}
    key = StringField()
    value = IntField()
    written_by = StringField()


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    async_client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = async_client[SPIKE_DB_NAME]

    print("== 0. clean slate, both clients open on the same collection ==")
    await db.drop_collection(COLLECTION)
    await init_beanie(database=db, document_models=[BeanieSide])
    disconnect()
    connect(db=SPIKE_DB_NAME, host=connection_string, alias="default")
    print("  AsyncMongoClient (Beanie) and MongoClient (MongoEngine) both connected")

    print("\n== 1. interleaved writes, read by the other side ==")
    await BeanieSide(key="a", value=1, written_by="beanie").insert()
    MongoEngineSide(key="b", value=2, written_by="mongoengine").save()

    from_beanie = await BeanieSide.find_one(BeanieSide.key == "b")
    from_mongoengine = MongoEngineSide.objects(key="a").first()
    print(f"  Beanie reads MongoEngine's doc      : {from_beanie.key if from_beanie else 'FAILED'} "
          f"value={from_beanie.value if from_beanie else '-'}")
    print(f"  MongoEngine reads Beanie's doc      : {from_mongoengine.key if from_mongoengine else 'FAILED'} "
          f"value={from_mongoengine.value if from_mongoengine else '-'}")

    print("\n== 2. write by one, update by the other, read back by the first ==")
    MongoEngineSide.objects(key="a").update(set__value=99)
    reread = await BeanieSide.find_one(BeanieSide.key == "a")
    print(f"  Beanie doc updated by MongoEngine   : value={reread.value} (expect 99)")

    print("\n== 3. connection counts ==")
    server_status: dict[str, Any] = await async_client.admin.command("serverStatus")
    connections = server_status.get("connections", {})
    print(f"  server reports: {connections}")

    print("\n== 4. does the SYNC half still block the event loop? ==")
    print("   A background task ticks every 10ms. A blocking MongoEngine read runs on the loop.")

    ticks = 0
    stop = False

    async def ticker() -> None:
        nonlocal ticks
        while not stop:
            ticks += 1
            await asyncio.sleep(0.01)

    task = asyncio.create_task(ticker())
    await asyncio.sleep(0.2)
    baseline = ticks
    print(f"  ticks in a free 200ms window                 : {baseline}")

    ticks = 0
    started = time.perf_counter()
    for _ in range(200):
        MongoEngineSide.objects(key="a").first()  # blocking, on the loop thread
    blocking_elapsed = time.perf_counter() - started
    blocked_ticks = ticks
    print(f"  200 blocking MongoEngine reads took          : {blocking_elapsed * 1000:.0f}ms")
    print(f"  ticks during that window                     : {blocked_ticks} "
          f"(expect ~{int(blocking_elapsed / 0.01)} if the loop were free)")

    ticks = 0
    started = time.perf_counter()
    for _ in range(200):
        await BeanieSide.find_one(BeanieSide.key == "a")
    async_elapsed = time.perf_counter() - started
    async_ticks = ticks
    print(f"  200 async Beanie reads took                  : {async_elapsed * 1000:.0f}ms")
    print(f"  ticks during that window                     : {async_ticks} "
          f"(expect ~{int(async_elapsed / 0.01)} if the loop stayed free)")

    stop = True
    await task

    print("\n== 5. verdict on loop starvation ==")
    print(f"  blocking path starved the loop: {blocked_ticks < int(blocking_elapsed / 0.01) * 0.5}")
    print(f"  async path kept the loop alive: {async_ticks >= int(async_elapsed / 0.01) * 0.5}")

    disconnect()
    await async_client.close()


if __name__ == "__main__":
    asyncio.run(main())
