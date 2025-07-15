from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, EmbeddedDocumentField, StringField

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleStringEntity


class AgentConfigEntity(Document):
    """Stores a specific, named configuration for an agent class."""

    meta = {
        "collection": "agent_configs",
        "indexes": [{"fields": ("agent_class", "agent_id"), "unique": True}],
    }

    config_class = StringField(required=True)
    agent_class = StringField(required=True)
    agent_id = StringField(required=True, description="Unique, URL-safe ID for the agent instance (e.g., 'agent_123').")
    name = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Name of the agent, used for display in the UI."
    )
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Description of the agent's purpose or functionality."
    )
    icon = StringField(required=True, description="Icon representing the agent, e.g., 'meteor-icons:robot'.")
    color = StringField(required=False, description="UI theme color for the agent.", null=True)
    voice = StringField(required=False, description="TTS voice ID used by the agent.", null=True)
    system_prompt = EmbeddedDocumentField(
        LocaleStringEntity,
        required=True,
        description="The system prompt that guides the agent's behavior and responses.",
    )
    config_data = DictField(required=True, description="The configuration data matching the Pydantic model.")
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    @classmethod
    def find_for_class(cls, agent_class: str) -> list["AgentConfigEntity"]:
        """Find all configurations for a specific agent class."""
        return cls.objects(agent_class=agent_class)

    @classmethod
    def find_for_class_and_id(cls, agent_class: str, agent_id: str) -> "AgentConfigEntity | None":
        """Find a specific configuration by agent class and ID."""
        return cls.objects(agent_class=agent_class, agent_id=agent_id).first()

    def save(self, *args, **kwargs):
        """Override save to update the updated_at timestamp."""
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    @classmethod
    def from_agent_config(cls, agent_config: AgentConfig) -> "AgentConfigEntity":
        """Create an instance entity from an AgentConfig."""
        return cls(
            config_class=agent_config.config_name_from_class(),
            agent_class=agent_config.agent_class,
            agent_id=agent_config.agent_id,
            name=LocaleStringEntity.from_locale_string(agent_config.name),
            description=LocaleStringEntity.from_locale_string(agent_config.description),
            icon=agent_config.icon,
            color=agent_config.color,
            voice=agent_config.voice,
            system_prompt=LocaleStringEntity.from_locale_string(agent_config.system_prompt),
            config_data=agent_config.model_dump(),
        )

    def update_from_agent_config(self, agent_config: AgentConfig) -> "AgentConfigEntity":
        """Update an existing instance entity from an AgentConfig."""
        self.config_class = agent_config.config_name_from_class()
        self.agent_class = agent_config.agent_class
        self.agent_id = agent_config.agent_id
        self.name = LocaleStringEntity.from_locale_string(agent_config.name)
        self.description = LocaleStringEntity.from_locale_string(agent_config.description)
        self.icon = agent_config.icon
        self.color = agent_config.color
        self.voice = agent_config.voice
        self.system_prompt = LocaleStringEntity.from_locale_string(agent_config.system_prompt)
        self.config_data = agent_config.model_dump()
        return self
