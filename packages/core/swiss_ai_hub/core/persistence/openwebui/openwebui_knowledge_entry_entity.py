from typing import Self

from mongoengine import BooleanField, Document, StringField

from swiss_ai_hub.core.events.agent.user.knowledge_reference import KnowledgeReference


class OpenWebuiKnowledgeEntryEntity(Document):
    """Which OpenWebUI knowledge entry stands for which of our collections.

    OpenWebUI assigns its own ids and keeps no field we can write for its knowledge entries, so the link lives here:
    the sync finds the entry to update or remove through it, and a referenced entry resolves to our collection.

    Every id ever issued stays recorded, only one of them current per collection. Chats keep sending the id they
    referenced after the sync replaced or removed that entry, and only a recorded id tells the agent which collection
    the user meant: a removed collection is then named as unavailable, a replaced entry still finds its collection.
    """

    meta = {
        "collection": "openwebui_knowledge_entries",
        "indexes": [
            {"fields": ["openwebui_id"], "unique": True},
            {"fields": ["database", "namespace", "current"]},
        ],
    }

    openwebui_id = StringField(required=True)
    database = StringField(required=True)
    namespace = StringField(required=True)
    current = BooleanField(default=True)

    @property
    def reference(self) -> KnowledgeReference:
        return KnowledgeReference(database=self.database, namespace=self.namespace)

    @classmethod
    def current_entries(cls) -> list[Self]:
        """The entry each collection is listed under in OpenWebUI now."""
        return list(cls.objects(current=True))

    @classmethod
    def record(cls, openwebui_id: str, reference: KnowledgeReference) -> Self:
        """Makes this entry the collection's current one; the entry it replaces keeps resolving to the collection."""
        cls.objects(database=reference.database, namespace=reference.namespace, current=True).update(set__current=False)
        return cls(openwebui_id=openwebui_id, database=reference.database, namespace=reference.namespace).save()

    @classmethod
    def retire(cls, openwebui_id: str) -> None:
        """The entry is no longer listed in OpenWebUI, but chats that referenced it still resolve."""
        cls.objects(openwebui_id=openwebui_id).update(set__current=False)

    @classmethod
    def references_for(cls, openwebui_ids: list[str]) -> list[KnowledgeReference]:
        """Our collections behind these entries, in the order given, including entries the sync since replaced or
        removed; an id we did not create resolves to nothing."""
        by_id = {entry.openwebui_id: entry.reference for entry in cls.objects(openwebui_id__in=openwebui_ids)}
        return [by_id[openwebui_id] for openwebui_id in openwebui_ids if openwebui_id in by_id]
