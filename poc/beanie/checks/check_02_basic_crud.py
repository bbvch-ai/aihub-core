"""Check 02 — basic CRUD through Beanie, and the on-disk shape against MongoEngine.

The floor test. The half that actually decides something is the shape comparison:
an incremental migration means both ODMs read and write the same collections for a
period, so a difference in stored shape is not cosmetic — it decides whether
incremental migration is possible at all.

Both documents are written to the SAME collection and read back with a plain
synchronous PyMongo client, so neither ODM's deserialization can hide a difference.
"""

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any

import pymongo
from beanie import Document, init_beanie
from mongoengine import connect, disconnect
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient, MongoClient

from swiss_ai_hub.core.i18n.locale_string import LocaleString as CoreLocaleString
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "crud_shape"


class LocaleString(BaseModel):
    de: str | None = None
    en: str | None = None
    fr: str | None = None
    it: str | None = None


class AgentConfigDoc(Document):
    agent_class: str
    agent_id: str
    name: LocaleString
    description: LocaleString
    icon: str
    config_data: dict[str, Any]
    created_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]
    updated_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(UTC))]

    class Settings:
        name = COLLECTION
        indexes = [
            pymongo.IndexModel(
                [("agent_class", pymongo.ASCENDING), ("agent_id", pymongo.ASCENDING)],
                unique=True,
                name="agent_class_1_agent_id_1",
            )
        ]


def describe(document: dict[str, Any], indent: str = "  ") -> str:
    lines = []
    for key in sorted(document):
        value = document[key]
        lines.append(f"{indent}{key:<14} {type(value).__name__:<12} {value!r}")
    return "\n".join(lines)


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    async_client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = async_client[SPIKE_DB_NAME]

    print("== 0. clean slate ==")
    await db.drop_collection(COLLECTION)
    await init_beanie(database=db, document_models=[AgentConfigDoc])
    print(f"{SPIKE_DB_NAME}.{COLLECTION} dropped and initialised")

    print("\n== 1. Beanie: insert ==")
    beanie_doc = AgentConfigDoc(
        agent_class="RAGAgent",
        agent_id="via-beanie",
        name=LocaleString(en="Beanie agent", de="Beanie-Agent"),
        description=LocaleString(en="Written by Beanie"),
        icon="mage:robot",
        config_data={"temperature": 0.7, "nested": {"a": {"b": 1}}},
    )
    await beanie_doc.insert()
    print(f"inserted _id={beanie_doc.id!r} type={type(beanie_doc.id).__name__}")

    print("\n== 2. Beanie: find_one ==")
    found = await AgentConfigDoc.find_one(AgentConfigDoc.agent_id == "via-beanie")
    print(f"found: agent_id={found.agent_id} name.en={found.name.en} config_data={found.config_data}")

    print("\n== 3. Beanie: modify and save ==")
    found.icon = "mage:robot-modified"
    found.config_data["temperature"] = 0.2
    await found.save()
    reread = await AgentConfigDoc.find_one(AgentConfigDoc.agent_id == "via-beanie")
    print(f"after save: icon={reread.icon} temperature={reread.config_data['temperature']}")

    print("\n== 4. MongoEngine: insert into the SAME collection ==")
    disconnect()
    connect(db=SPIKE_DB_NAME, host=connection_string, alias="default")
    AgentConfigEntityDocument._meta["collection"] = COLLECTION
    mongoengine_doc = AgentConfigEntityDocument(
        agent_class="RAGAgent",
        agent_id="via-mongoengine",
        name=LocaleStringEntity.from_locale_string(CoreLocaleString(en="ME agent", de="ME-Agent")),
        description=LocaleStringEntity.from_locale_string(CoreLocaleString(en="Written by MongoEngine")),
        icon="mage:robot",
        config_data={"temperature": 0.7, "nested": {"a": {"b": 1}}},
    )
    mongoengine_doc.save()
    print(f"inserted _id={mongoengine_doc.id!r} type={type(mongoengine_doc.id).__name__}")

    print("\n== 5. raw BSON of both, read with a plain PyMongo client ==")
    sync_client: MongoClient = MongoClient(connection_string)
    raw = sync_client[SPIKE_DB_NAME][COLLECTION]
    beanie_raw = raw.find_one({"agent_id": "via-beanie"})
    mongoengine_raw = raw.find_one({"agent_id": "via-mongoengine"})

    print("\n-- written by Beanie --")
    print(describe(beanie_raw))
    print("\n-- written by MongoEngine --")
    print(describe(mongoengine_raw))

    print("\n== 6. key-set difference ==")
    beanie_keys, mongoengine_keys = set(beanie_raw), set(mongoengine_raw)
    print(f"only in Beanie doc      : {sorted(beanie_keys - mongoengine_keys)}")
    print(f"only in MongoEngine doc : {sorted(mongoengine_keys - beanie_keys)}")
    print(f"shared                  : {sorted(beanie_keys & mongoengine_keys)}")

    print("\n== 7. cross-read: can each ODM read the other's document? ==")
    cross = await AgentConfigDoc.find_one(AgentConfigDoc.agent_id == "via-mongoengine")
    print(f"Beanie reading MongoEngine's doc : {'OK' if cross else 'FAILED'}", end="")
    if cross:
        print(f" (name.en={cross.name.en!r} created_at={cross.created_at!r})")
    cross_back = AgentConfigEntityDocument.objects(agent_id="via-beanie").first()
    print(f"MongoEngine reading Beanie's doc : {'OK' if cross_back else 'FAILED'}", end="")
    if cross_back:
        print(f" (name.en={cross_back.name.en!r} created_at={cross_back.created_at!r})")

    sync_client.close()
    disconnect()
    await async_client.close()


if __name__ == "__main__":
    asyncio.run(main())
