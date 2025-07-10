from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, StringField


class AgentConfigInstanceEntity(Document):
    """Stores a specific, named configuration for an agent class."""

    meta = {
        "collection": "agent_config_instances",
        "indexes": [{"fields": ("agent_class", "config_id"), "unique": True}],
    }

    agent_class = StringField(required=True)
    config_id = StringField(
        required=True, description="Unique, URL-safe ID for the config (e.g., 'hr-policy-bot'). Becomes the agent_id."
    )
    config_name = StringField(required=True, description="User-friendly display name (e.g., 'HR Policy Bot').")
    description = StringField()
    config_data = DictField(required=True, description="The configuration data matching the Pydantic model.")
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    @classmethod
    def find_for_class(cls, agent_class: str) -> list["AgentConfigInstanceEntity"]:
        """Find all configurations for a specific agent class."""
        return cls.objects(agent_class=agent_class)

    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)
