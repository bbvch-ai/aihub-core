from datetime import datetime

from mongoengine import DateTimeField, Document

from aihub_lib.persistence.agents import AgentConfigEntity


class AgentConfigEntityDocument(AgentConfigEntity, Document):
    """
    This is the specific class for storing agent configurations in the `agent_configs` collection.
    It extends the base `AgentConfigEntity` class and uses MongoDB's Document model for persistence as
    a standalone collection.
    This is commonly used to store specific configurations defined in the MongoDB database by the user.
    """

    meta = {
        "collection": "agent_configs",
        "indexes": [{"fields": ("agent_class", "agent_id"), "unique": True}],
    }

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    @classmethod
    def find_for_class(cls, agent_class: str) -> list["AgentConfigEntityDocument"]:
        """Find all configurations for a specific agent class."""
        return cls.objects(agent_class=agent_class)

    @classmethod
    def find_for_class_and_id(cls, agent_class: str, agent_id: str) -> "AgentConfigEntityDocument | None":
        """Find a specific configuration by agent class and ID."""
        return cls.objects(agent_class=agent_class, agent_id=agent_id).first()

    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
