from typing import Self

from beanie import Document
from pymongo import ASCENDING, IndexModel

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class OpenWebuiKnowledgeEntryEntity(Document):
    """Which OpenWebUI knowledge entry stands for which of our collections.

    OpenWebUI assigns its own ids and keeps no field we can write for its knowledge entries, so the link lives here:
    the sync finds the entry to update or remove through it, and a referenced entry resolves to our collection.
    """

    openwebui_id: str
    database: str
    namespace: str

    class Settings:
        name = "openwebui_knowledge_entries"
        keep_nulls = False
        indexes = [
            IndexModel([("openwebui_id", ASCENDING)], unique=True),
            IndexModel([("database", ASCENDING), ("namespace", ASCENDING)], unique=True),
        ]

    @property
    def reference(self) -> KnowledgeReference:
        return KnowledgeReference(database=self.database, namespace=self.namespace)

    @classmethod
    @trace_fn
    async def all_entries(cls) -> list[Self]:
        return await cls.find().to_list()

    @classmethod
    @trace_fn
    async def record(cls, openwebui_id: str, reference: KnowledgeReference) -> Self:
        await cls.find({"database": reference.database, "namespace": reference.namespace}).delete()
        return await cls(openwebui_id=openwebui_id, database=reference.database, namespace=reference.namespace).insert()

    @classmethod
    @trace_fn
    async def forget(cls, openwebui_id: str) -> None:
        await cls.find({"openwebui_id": openwebui_id}).delete()

    @classmethod
    @trace_fn
    async def references_for(cls, openwebui_ids: list[str]) -> list[KnowledgeReference]:
        """Our collections behind these entries, in the order given; an id we did not create resolves to nothing."""
        entries = await cls.find({"openwebui_id": {"$in": openwebui_ids}}).to_list()
        by_id = {entry.openwebui_id: entry.reference for entry in entries}
        return [by_id[openwebui_id] for openwebui_id in openwebui_ids if openwebui_id in by_id]
