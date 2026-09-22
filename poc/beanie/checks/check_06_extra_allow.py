"""Check 06 — does a document with undeclared fields survive read-modify-write?

Four of our documents run with `strict: False` because old shapes drift:
ThreadEntity, PersistedAgentEventEntity, PersistedProcessEventEntity, UserDashboardEntity.

Loading such a document is the easy half. The half that matters is writing it back.
If Beanie drops undeclared fields on save, one read-modify-write silently deletes
production data that no code knew about -- and there is no migration framework in
place to have removed it deliberately (issue #1152).

Tested against all three write paths, because they may differ and `replace()` is
the dangerous one.
"""

import asyncio
from typing import Any

from beanie import Document, init_beanie
from pydantic import ConfigDict
from pymongo import AsyncMongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "extra_allow"

DECLARED = {"thread_id", "title"}
EXTRAS = {"legacy_owner", "removed_in_v2", "nested_legacy"}


class StrictDoc(Document):
    """No extra handling configured -- the default."""

    thread_id: str
    title: str

    class Settings:
        name = COLLECTION


class LenientDoc(Document):
    """The `strict: False` equivalent."""

    model_config = ConfigDict(extra="allow")

    thread_id: str
    title: str

    class Settings:
        name = COLLECTION
        use_state_management = True


async def seed(db: Any, thread_id: str) -> None:
    await db[COLLECTION].insert_one(
        {
            "thread_id": thread_id,
            "title": "original title",
            "legacy_owner": "someone@example.com",
            "removed_in_v2": 42,
            "nested_legacy": {"a": {"b": [1, 2, 3]}},
        }
    )


async def report(db: Any, thread_id: str, label: str) -> set[str]:
    stored = await db[COLLECTION].find_one({"thread_id": thread_id})
    keys = set(stored) - {"_id"}
    survived = keys & EXTRAS
    lost = EXTRAS - keys
    print(f"  {label}")
    print(f"    keys stored : {sorted(keys)}")
    print(f"    extras kept : {sorted(survived) or 'NONE'}")
    print(f"    extras LOST : {sorted(lost) or 'none'}")
    return lost


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = client[SPIKE_DB_NAME]

    print("== 0. clean slate ==")
    await db.drop_collection(COLLECTION)
    await init_beanie(database=db, document_models=[StrictDoc, LenientDoc])

    print("\n== 1. can a STRICT model even load a document with extras? ==")
    await seed(db, "strict-load")
    try:
        loaded = await StrictDoc.find_one(StrictDoc.thread_id == "strict-load")
        print(f"  loaded without error: title={loaded.title!r}")
        print("  -> Beanie does not reject unknown fields on read by default")
    except Exception as refused:  # noqa: BLE001 - the exception type is the finding
        print(f"  REFUSED: {type(refused).__name__}: {refused}")

    print("\n== 2. STRICT model: read -> modify -> save() ==")
    loaded = await StrictDoc.find_one(StrictDoc.thread_id == "strict-load")
    loaded.title = "modified by strict"
    await loaded.save()
    strict_lost = await report(db, "strict-load", "after StrictDoc.save()")

    print("\n== 3. LENIENT model (extra='allow'): are extras visible in Python? ==")
    await seed(db, "lenient-save")
    loaded = await LenientDoc.find_one(LenientDoc.thread_id == "lenient-save")
    print(f"  model_extra: {loaded.model_extra}")

    print("\n== 4. LENIENT model: read -> modify -> save() ==")
    loaded.title = "modified by lenient"
    await loaded.save()
    lenient_save_lost = await report(db, "lenient-save", "after LenientDoc.save()")

    print("\n== 5. LENIENT model: read -> modify -> save_changes() ==")
    await seed(db, "lenient-changes")
    loaded = await LenientDoc.find_one(LenientDoc.thread_id == "lenient-changes")
    loaded.title = "modified by save_changes"
    await loaded.save_changes()
    lenient_changes_lost = await report(db, "lenient-changes", "after LenientDoc.save_changes()")

    print("\n== 6. LENIENT model: read -> modify -> replace() ==")
    await seed(db, "lenient-replace")
    loaded = await LenientDoc.find_one(LenientDoc.thread_id == "lenient-replace")
    loaded.title = "modified by replace"
    await loaded.replace()
    lenient_replace_lost = await report(db, "lenient-replace", "after LenientDoc.replace()")

    print("\n== 6b. THE DANGEROUS COMBINATION: strict model + replace() ==")
    print("  StrictDoc discards extras on load, so if replace() writes the whole document")
    print("  back, the extras have nothing to come from. This is the case to fear.")
    await seed(db, "strict-replace")
    loaded = await StrictDoc.find_one(StrictDoc.thread_id == "strict-replace")
    print(f"  model_extra on strict model: {loaded.model_extra}")
    loaded.title = "modified by strict replace"
    await loaded.replace()
    strict_replace_lost = await report(db, "strict-replace", "after StrictDoc.replace()")

    print("\n== 7. summary ==")
    for label, lost in [
        ("StrictDoc.save()", strict_lost),
        ("StrictDoc.replace()", strict_replace_lost),
        ("LenientDoc.save()", lenient_save_lost),
        ("LenientDoc.save_changes()", lenient_changes_lost),
        ("LenientDoc.replace()", lenient_replace_lost),
    ]:
        verdict = "DATA LOSS" if lost else "safe"
        print(f"  {label:<30} {verdict:<10} {sorted(lost) if lost else ''}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
