from mongoengine import DictField, EmbeddedDocumentField, StringField
from mongoengine.base import BaseDocument

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


class AgentConfigEntity(BaseDocument):
    """
    This is the base class for storing an agent configuration.
    Never use this class directly; instead, use the `AgentConfigEntityDocument` or `AgentConfigEntityEmbeddedDocument`
    subclasses for persistence in MongoDB.
    This class is only used to define the common fields and methods for agent configs.
    """

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

    @classmethod
    def from_agent_config(cls, agent_config: AgentConfig) -> "AgentConfigEntity":
        """Create an instance entity from an AgentConfig."""
        return cls(
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
