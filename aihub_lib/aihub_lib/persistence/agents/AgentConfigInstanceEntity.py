from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, EmbeddedDocumentField, StringField

from aihub_lib.i18n.LocaleString import LocaleStringEntity


class AgentConfigInstanceEntity(Document):
    """Stores a specific, named configuration for an agent class."""

    meta = {
        "collection": "agent_config_instances",
        "indexes": [{"fields": ("agent_class", "agent_id"), "unique": True}],
    }

    agent_class = StringField(required=True)
    agent_id = StringField(required=True, description="Unique, URL-safe ID for the agent instance (e.g., 'agent_123').")
    name = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Name of the agent, used for display in the UI."
    )
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Description of the agent's purpose or functionality."
    )
    icon = StringField(required=True, description="Icon representing the agent, e.g., 'meteor-icons:robot'.")
    color: StringField(required=False, description="UI theme color for the agent.")
    voice: StringField(required=False, description="TTS voice ID used by the agent.")
    system_prompt = EmbeddedDocumentField(
        LocaleStringEntity,
        required=True,
        description="The system prompt that guides the agent's behavior and responses.",
    )
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
