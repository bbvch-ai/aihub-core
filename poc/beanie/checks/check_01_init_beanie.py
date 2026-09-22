"""Check 01 — does `init_beanie` complete against FerretDB 2.5, and are the indexes real?

Mirrors `AgentConfigEntityDocument`, the hardest index case in the codebase: a compound
unique index plus a plain secondary index on the same collection.

Verifying that `init_beanie` returns is not enough. A silently ignored unique index is
worse than a rejected one — the constraint would be gone with nothing to notice it — so
this also reads the indexes back server-side and tries to insert a genuine duplicate.
"""

import asyncio
import time
from datetime import UTC, datetime
from typing import Annotated, Any

import pymongo
from beanie import Document, init_beanie
from pydantic import BaseModel, Field
from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError

from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings

SPIKE_DB_NAME = "aihub_beanie_spike"
COLLECTION = "agent_configs"


class LocaleString(BaseModel):
    de: str | None = None
    en: str | None = None
    fr: str | None = None
    it: str | None = None


class AgentConfigDoc(Document):
    """Beanie equivalent of AgentConfigEntityDocument."""

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
            ),
            pymongo.IndexModel([("agent_class", pymongo.ASCENDING)], name="agent_class_1"),
        ]


def sample(agent_id: str) -> AgentConfigDoc:
    return AgentConfigDoc(
        agent_class="RAGAgent",
        agent_id=agent_id,
        name=LocaleString(en="Test agent", de="Testagent"),
        description=LocaleString(en="A spike document"),
        icon="mage:robot",
        config_data={"temperature": 0.7, "nested": {"a": {"b": 1}}},
    )


async def main() -> None:
    connection_string = MongoSettings().CONNECTION_STRING.get_secret_value()
    client: AsyncMongoClient = AsyncMongoClient(connection_string)
    db = client[SPIKE_DB_NAME]

    print("== 0. clean slate ==")
    await db.drop_collection(COLLECTION)
    print(f"dropped {SPIKE_DB_NAME}.{COLLECTION}")

    print("\n== 1. init_beanie (cold, collection absent) ==")
    started = time.perf_counter()
    await init_beanie(database=db, document_models=[AgentConfigDoc])
    print(f"returned without error in {time.perf_counter() - started:.3f}s")

    print("\n== 2. indexes as FerretDB reports them ==")
    async for index in await db[COLLECTION].list_indexes():
        print(dict(index))

    print("\n== 3. is the unique constraint actually enforced? ==")
    await sample("spike-a").insert()
    print("inserted spike-a")
    try:
        await sample("spike-a").insert()
        print("RESULT: second insert SUCCEEDED -> unique index is NOT enforced")
    except DuplicateKeyError as duplicate:
        print(f"RESULT: second insert rejected -> unique index IS enforced ({type(duplicate).__name__})")

    print("\n== 4. a different agent_id on the same class must still be allowed ==")
    await sample("spike-b").insert()
    print("inserted spike-b (compound index behaves as compound, not as unique-on-agent_class)")

    print("\n== 5. init_beanie again (warm, collection and indexes exist) ==")
    started = time.perf_counter()
    await init_beanie(database=db, document_models=[AgentConfigDoc])
    print(f"returned without error in {time.perf_counter() - started:.3f}s -> idempotent")

    print("\n== 6. index count unchanged after re-init ==")
    names = sorted([dict(i)["name"] async for i in await db[COLLECTION].list_indexes()])
    print(names)

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
