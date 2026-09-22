"""Check 07 — what is actually stored for a datetime, and how far apart are the ODMs?

This sizes a data migration. The codebase is already inconsistent with itself:

  AgentClassEntity.last_discovered   default=datetime.now        -> naive LOCAL
  AgentConfigEntityDocument.created_at  default=datetime.now(UTC) -> aware UTC

`is_online` compares `datetime.now() - last_discovered < ONLINE_THRESHOLD`
(agent_class_entity.py:110). The docstring at :257 spells out the consequence of
getting the zone wrong: on a host ahead of UTC every dead class reads online, on a
host behind UTC nothing ever fires.

MUST be run on a host that is NOT on UTC, or it proves nothing. This host is UTC+7
(see ../environment.md).
"""

import asyncio
import time
from datetime import UTC, datetime, timedelta

from beanie import Document, init_beanie
from mongoengine import DateTimeField, Document as MEDocument, StringField, connect, disconnect
from pymongo import AsyncMongoClient, MongoClient

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "datetime_shape"
ONLINE_THRESHOLD = timedelta(minutes=5)


class BeanieStamp(Document):
    label: str
    stamp: datetime

    class Settings:
        name = COLLECTION


class MEStamp(MEDocument):
    meta = {"collection": COLLECTION, "strict": False}
    label = StringField()
    stamp = DateTimeField()


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    offset_hours = -time.timezone // 3600
    print(f"host UTC offset: {offset_hours:+d}h  (a UTC host would make this check meaningless)")

    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = client[SPIKE_DB_NAME]
    await db.drop_collection(COLLECTION)
    await init_beanie(database=db, document_models=[BeanieStamp])

    naive_local = datetime.now()
    aware_utc = datetime.now(UTC)
    print("\n== 0. the two values, in Python ==")
    print(f"  datetime.now()     -> {naive_local!r}")
    print(f"  datetime.now(UTC)  -> {aware_utc!r}")
    print(f"  difference         -> {(naive_local - aware_utc.replace(tzinfo=None)).total_seconds() / 3600:.1f}h")

    print("\n== 1. write both through Beanie ==")
    await BeanieStamp(label="beanie_naive_local", stamp=naive_local).insert()
    await BeanieStamp(label="beanie_aware_utc", stamp=aware_utc).insert()

    print("== 2. write both through MongoEngine ==")
    disconnect()
    connect(db=SPIKE_DB_NAME, host=connection_string, alias="default")
    MEStamp(label="mongoengine_naive_local", stamp=naive_local).save()
    MEStamp(label="mongoengine_aware_utc", stamp=aware_utc).save()

    print("\n== 3. raw BSON, read with a plain PyMongo client (tz_aware=False, the default) ==")
    sync_client: MongoClient = MongoClient(connection_string)
    raw = sync_client[SPIKE_DB_NAME][COLLECTION]
    for document in raw.find({}, sort=[("label", 1)]):
        stamp = document["stamp"]
        print(f"  {document['label']:<26} {stamp!r}  tzinfo={stamp.tzinfo}")

    print("\n== 4. same documents, read with tz_aware=True ==")
    aware_client: MongoClient = MongoClient(connection_string, tz_aware=True)
    for document in aware_client[SPIKE_DB_NAME][COLLECTION].find({}, sort=[("label", 1)]):
        print(f"  {document['label']:<26} {document['stamp']!r}")

    print("\n== 5. what comes back through each ODM ==")
    async for document in BeanieStamp.find_all():
        print(f"  Beanie      {document.label:<26} {document.stamp!r} tzinfo={document.stamp.tzinfo}")
    for document in MEStamp.objects():
        print(f"  MongoEngine {document.label:<26} {document.stamp!r} tzinfo={document.stamp.tzinfo}")

    print("\n== 6. the is_online comparison, as agent_class_entity.py:110 performs it ==")
    print("   `datetime.now() - last_discovered < ONLINE_THRESHOLD`, freshly written = must be ONLINE")
    async for document in BeanieStamp.find_all():
        stored = document.stamp
        comparable = stored.replace(tzinfo=None) if stored.tzinfo else stored
        age = datetime.now() - comparable
        online = age < ONLINE_THRESHOLD
        verdict = "ONLINE (correct)" if online else f"OFFLINE (WRONG, age={age})"
        print(f"  {document.label:<26} age={str(age):<20} {verdict}")

    print("\n== 7. and the reverse error: comparing against an aware UTC now ==")
    for document in MEStamp.objects():
        stored = document.stamp
        comparable = stored.replace(tzinfo=None) if stored.tzinfo else stored
        age = datetime.now(UTC).replace(tzinfo=None) - comparable
        online = age < ONLINE_THRESHOLD
        verdict = "ONLINE" if online else f"OFFLINE (age={age})"
        print(f"  {document.label:<26} age={str(age):<20} {verdict}")

    sync_client.close()
    aware_client.close()
    disconnect()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
