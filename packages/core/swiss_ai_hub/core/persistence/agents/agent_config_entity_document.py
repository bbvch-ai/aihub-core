from datetime import UTC, datetime

from mongoengine import DateTimeField, Document, Q

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.agents import AgentConfigEntity


class AgentConfigEntityDocument(AgentConfigEntity, Document):
    """
    This is the specific class for storing agent configurations in the `agent_configs` collection.
    It extends the base `AgentConfigEntity` class and uses MongoDB's Document model for persistence as
    a standalone collection.
    This is commonly used to store specific configurations defined in the MongoDB database by the user.
    """

    meta = {
        "collection": "agent_configs",
        "indexes": [
            {"fields": ("agent_class", "agent_id"), "unique": True},
            {"fields": ["agent_class"]},
        ],
    }

    created_at = DateTimeField(default=lambda: datetime.now(UTC))
    updated_at = DateTimeField(default=lambda: datetime.now(UTC))

    @classmethod
    @trace_fn
    def find_for_classes(cls, agent_classes: list[str]) -> list["AgentConfigEntityDocument"]:
        return list(cls.objects(agent_class__in=agent_classes))

    @classmethod
    @trace_fn
    def find_for_class(cls, agent_class: str) -> list["AgentConfigEntityDocument"]:
        """Find all configurations for a specific agent class."""
        return cls.objects(agent_class=agent_class)

    @classmethod
    @trace_fn
    def find_for_name(cls, agent_class: str, name: str | None = None) -> list["AgentConfigEntityDocument"]:
        if name is None:
            return list(cls.find_for_class(agent_class))
        name_matches = (
            Q(name__de__icontains=name)
            | Q(name__en__icontains=name)
            | Q(name__fr__icontains=name)
            | Q(name__it__icontains=name)
        )
        queryset = cls.objects(name_matches, agent_class=agent_class)

        return list(queryset)

    @classmethod
    @trace_fn
    def find_for_class_and_id(cls, agent_class: str, agent_id: str) -> "AgentConfigEntityDocument | None":
        """Find a specific configuration by agent class and ID."""
        return cls.objects(agent_class=agent_class, agent_id=agent_id).first()

    @classmethod
    @trace_fn
    def delete_if_exists_for_class_and_id(cls, agent_class: str, agent_id: str) -> None:
        """Delete a specific configuration by agent class and ID if it exists."""
        existing = cls.find_for_class_and_id(agent_class, agent_id)
        if existing:
            existing.delete()

    @trace_fn
    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)
        return super().save(*args, **kwargs)
