from typing import Self

from mongoengine import Document, StringField

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference


class OpenWebuiKnowledgeEntryEntity(Document):
    """Which OpenWebUI knowledge entry stands for which of our collections.

    OpenWebUI assigns its own ids and keeps no field we can write for its knowledge entries, so the link lives here:
    the sync finds the entry to update or remove through it, and a referenced entry resolves to our collection.
    """

    meta = {
        "collection": "openwebui_knowledge_entries",
        "indexes": [{"fields": ["openwebui_id"], "unique": True}, {"fields": ["database", "namespace"], "unique": True}],
    }

    openwebui_id = StringField(required=True)
    database = StringField(required=True)
    namespace = StringField(required=True)

    @property
    def reference(self) -> KnowledgeReference:
        return KnowledgeReference(database=self.database, namespace=self.namespace)

    @classmethod
    def all_entries(cls) -> list[Self]:
        return list(cls.objects())

    @classmethod
    def record(cls, openwebui_id: str, reference: KnowledgeReference) -> Self:
        cls.objects(database=reference.database, namespace=reference.namespace).delete()
        return cls(openwebui_id=openwebui_id, database=reference.database, namespace=reference.namespace).save()

    @classmethod
    def forget(cls, openwebui_id: str) -> None:
        cls.objects(openwebui_id=openwebui_id).delete()

    @classmethod
    def references_for(cls, openwebui_ids: list[str]) -> list[KnowledgeReference]:
        """Our collections behind these entries, in the order given; an id we did not create resolves to nothing."""
        by_id = {entry.openwebui_id: entry.reference for entry in cls.objects(openwebui_id__in=openwebui_ids)}
        return [by_id[openwebui_id] for openwebui_id in openwebui_ids if openwebui_id in by_id]
