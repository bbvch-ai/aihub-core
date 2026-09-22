"""Check 05 — how does Beanie express what MongoEngine's `switch_db` does for us?

MongoEngine binds a Document to an alias and lets a call-time context manager or
`instance.switch_db(db)` retarget it. Beanie binds a Document class to one database
at `init_beanie` time. Event persistence and RAG document storage both depend on
the MongoEngine behaviour:

  persisted_agent_event_entity.py:177   persisted_entity.switch_db(db)
  persisted_process_event_entity.py:46  persisted_entity.switch_db(db)
  ref_doc.py:17/192/366                 with switch_db(RefDoc, DB_ALIAS) as SwitchedRefDoc

Three candidate approaches are tried, in the order the check file states.
The question is not "does one work" but "what does the working one cost".
"""

import asyncio
import time
from typing import Any

from beanie import Document, init_beanie
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

DB_A = "aihub_beanie_spike"
DB_B = "aihub_beanie_spike_tenant_b"
COLLECTION = "routed_events"


class RoutedEvent(Document):
    event_id: str
    payload: dict[str, Any]

    class Settings:
        name = COLLECTION


async def approach_1_per_database_class(connection_string: str) -> None:
    """Initialise a separate Document subclass per database, once, at startup."""

    class RoutedEventA(RoutedEvent):
        class Settings:
            name = COLLECTION

    class RoutedEventB(RoutedEvent):
        class Settings:
            name = COLLECTION

    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    await init_beanie(database=client[DB_A], document_models=[RoutedEventA])
    await init_beanie(database=client[DB_B], document_models=[RoutedEventB])

    await RoutedEventA(event_id="in-a", payload={"db": "A"}).insert()
    await RoutedEventB(event_id="in-b", payload={"db": "B"}).insert()

    in_a = [d.event_id async for d in RoutedEventA.find_all()]
    in_b = [d.event_id async for d in RoutedEventB.find_all()]
    print(f"  db A contains: {sorted(in_a)}")
    print(f"  db B contains: {sorted(in_b)}")
    print(f"  isolated correctly: {in_a == ['in-a'] and in_b == ['in-b']}")
    print("  cost: one extra subclass + one init_beanie per database, known at startup")
    await client.close()


async def approach_2_raw_collection(connection_string: str) -> None:
    """Keep one Document class; drop to the underlying PyMongo collection to route."""
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    await init_beanie(database=client[DB_A], document_models=[RoutedEvent])

    document = RoutedEvent(event_id="raw-to-b", payload={"db": "B"})
    encoded = document.model_dump(by_alias=True, exclude={"id"})
    await client[DB_B][COLLECTION].insert_one(encoded)
    print(f"  wrote to db B via raw collection: {encoded['event_id']}")

    found = await client[DB_B][COLLECTION].find_one({"event_id": "raw-to-b"})
    rehydrated = RoutedEvent.model_validate(found)
    print(f"  read back and rehydrated: {rehydrated.event_id} payload={rehydrated.payload}")
    print(f"  leaked into db A: {await client[DB_A][COLLECTION].find_one({'event_id': 'raw-to-b'}) is not None}")
    print("  cost: manual encode/decode, no Beanie validation on write, no hooks, no typed query API")
    await client.close()


async def approach_3_reinit_per_call(connection_string: str) -> None:
    """Re-initialise the Document against another database per call. Expected to be unacceptable."""
    client: AsyncMongoClient = AsyncMongoClient(connection_string)

    started = time.perf_counter()
    iterations = 20
    for index in range(iterations):
        target = DB_A if index % 2 == 0 else DB_B
        await init_beanie(database=client[target], document_models=[RoutedEvent])
        await RoutedEvent(event_id=f"reinit-{index}", payload={"db": target}).insert()
    elapsed = time.perf_counter() - started
    print(f"  {iterations} routed writes via re-init: {elapsed:.3f}s ({elapsed / iterations * 1000:.1f} ms/write)")

    count_a = await client[DB_A][COLLECTION].count_documents({"event_id": {"$regex": "^reinit-"}})
    count_b = await client[DB_B][COLLECTION].count_documents({"event_id": {"$regex": "^reinit-"}})
    print(f"  landed in A: {count_a}, in B: {count_b} (expect 10 / 10)")
    print("  cost: mutates PROCESS-WIDE class state; unsafe under concurrency")
    await client.close()


async def concurrency_probe(connection_string: str) -> None:
    """Does approach 3 actually break when two routed writes interleave on one loop?"""
    client: AsyncMongoClient = AsyncMongoClient(connection_string)

    async def routed_write(target: str, event_id: str) -> None:
        await init_beanie(database=client[target], document_models=[RoutedEvent])
        await asyncio.sleep(0.01)  # a yield between binding and writing is all it takes
        await RoutedEvent(event_id=event_id, payload={"intended": target}).insert()

    await asyncio.gather(routed_write(DB_A, "race-to-a"), routed_write(DB_B, "race-to-b"))

    for event_id, intended in [("race-to-a", DB_A), ("race-to-b", DB_B)]:
        in_a = await client[DB_A][COLLECTION].find_one({"event_id": event_id}) is not None
        in_b = await client[DB_B][COLLECTION].find_one({"event_id": event_id}) is not None
        landed = DB_A if in_a else (DB_B if in_b else "nowhere")
        verdict = "OK" if landed == intended else "MISROUTED"
        print(f"  {event_id}: intended={intended} landed={landed} -> {verdict}")
    await client.close()


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    await client[DB_A].drop_collection(COLLECTION)
    await client[DB_B].drop_collection(COLLECTION)
    await client.close()

    print("== approach 1: one initialised Document subclass per database ==")
    await approach_1_per_database_class(connection_string)

    print("\n== approach 2: one class, route by dropping to the raw collection ==")
    await approach_2_raw_collection(connection_string)

    print("\n== approach 3: re-init the Document per call ==")
    await approach_3_reinit_per_call(connection_string)

    print("\n== approach 3 under concurrency: two routed writes on one event loop ==")
    await concurrency_probe(connection_string)


if __name__ == "__main__":
    asyncio.run(main())
