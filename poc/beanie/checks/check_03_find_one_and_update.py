"""Check 03 — does FerretDB 2.5 support the findAndModify path Beanie uses for updates?

Not optional in Beanie: `save_changes()` and the `set`/`update` helpers route through
`find_one_and_update`. If FerretDB does not implement it with the semantics Beanie
expects, every write path would have to be rewritten as a plain replace.

Also exercises the shapes our own code depends on today, notably the nested-field set
used by `ref_doc.py:366` (`update_one(set__data__metadata__is_ingested=True)`).
"""

import asyncio
from typing import Any

import pymongo
from beanie import Document, init_beanie
from beanie.odm.operators.update.general import Set
from pymongo import AsyncMongoClient, ReturnDocument

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "find_one_and_update"


class RefDocLike(Document):
    """Shaped after RefDoc: a deeply nested `data.metadata.*` the code updates in place."""

    ref_doc_id: str
    data: dict[str, Any]
    counter: int = 0

    class Settings:
        name = COLLECTION
        indexes = [pymongo.IndexModel([("ref_doc_id", pymongo.ASCENDING)], unique=True, name="ref_doc_id_1")]


class RefDocStateful(Document):
    """Same document, with state management on — the prerequisite for `save_changes()`."""

    ref_doc_id: str
    data: dict[str, Any]
    counter: int = 0

    class Settings:
        name = COLLECTION
        use_state_management = True


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = client[SPIKE_DB_NAME]

    print("== 0. clean slate ==")
    await db.drop_collection(COLLECTION)
    await init_beanie(database=db, document_models=[RefDocLike, RefDocStateful])

    await RefDocLike(
        ref_doc_id="doc-1",
        data={"metadata": {"is_ingested": False, "source": "spike"}, "text": "hello"},
    ).insert()
    print("inserted doc-1")

    raw = db[COLLECTION]

    print("\n== 1. driver-level find_one_and_update, plain field set ==")
    result = await raw.find_one_and_update(
        {"ref_doc_id": "doc-1"}, {"$set": {"counter": 1}}, return_document=ReturnDocument.AFTER
    )
    print(f"returned (AFTER) : counter={result['counter']}")
    result_before = await raw.find_one_and_update(
        {"ref_doc_id": "doc-1"}, {"$set": {"counter": 2}}, return_document=ReturnDocument.BEFORE
    )
    print(f"returned (BEFORE): counter={result_before['counter']}")
    current = await raw.find_one({"ref_doc_id": "doc-1"})
    print(f"stored now       : counter={current['counter']}  -> BEFORE/AFTER semantics correct")

    print("\n== 2. nested-field set (the ref_doc.py:366 shape) ==")
    result = await raw.find_one_and_update(
        {"ref_doc_id": "doc-1"},
        {"$set": {"data.metadata.is_ingested": True}},
        return_document=ReturnDocument.AFTER,
    )
    print(f"data.metadata    : {result['data']['metadata']}")
    print(f"siblings intact  : text={result['data'].get('text')!r}")

    print("\n== 3. upsert ==")
    result = await raw.find_one_and_update(
        {"ref_doc_id": "doc-upserted"},
        {"$set": {"data": {"metadata": {}}, "counter": 99}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    print(f"upserted _id={result['_id']!r} type={type(result['_id']).__name__} counter={result['counter']}")

    print("\n== 4. no-match without upsert returns None ==")
    result = await raw.find_one_and_update({"ref_doc_id": "absent"}, {"$set": {"counter": 1}})
    print(f"returned: {result!r}")

    print("\n== 5. Beanie API: .set() ==")
    doc = await RefDocLike.find_one(RefDocLike.ref_doc_id == "doc-1")
    await doc.set({RefDocLike.counter: 42})
    reread = await RefDocLike.find_one(RefDocLike.ref_doc_id == "doc-1")
    print(f"after .set()     : counter={reread.counter}")

    print("\n== 6a. save_changes() WITHOUT state management ==")
    doc = await RefDocLike.find_one(RefDocLike.ref_doc_id == "doc-1")
    doc.counter = 7
    try:
        await doc.save_changes()
        print("succeeded -- state management is not required")
    except Exception as refused:  # noqa: BLE001 - the exception type is the finding
        print(f"refused by Beanie: {type(refused).__name__}: {refused}")
        print("-> save_changes() is NOT available by default; it is opt-in per Document")

    print("\n== 6b. save_changes() WITH use_state_management = True ==")
    stateful = await RefDocStateful.find_one(RefDocStateful.ref_doc_id == "doc-1")
    stateful.counter = 7
    stateful.data["metadata"]["source"] = "changed"
    await stateful.save_changes()
    reread = await RefDocStateful.find_one(RefDocStateful.ref_doc_id == "doc-1")
    print(f"after save_changes: counter={reread.counter} metadata={reread.data['metadata']}")

    print("\n== 6c. does state management change the stored shape? ==")
    stored = await raw.find_one({"ref_doc_id": "doc-1"})
    print(f"keys: {sorted(stored)}")

    print("\n== 7. Beanie API: query-level update with Set ==")
    await RefDocLike.find(RefDocLike.ref_doc_id == "doc-1").update(Set({RefDocLike.counter: 100}))
    reread = await RefDocLike.find_one(RefDocLike.ref_doc_id == "doc-1")
    print(f"after query update: counter={reread.counter}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
