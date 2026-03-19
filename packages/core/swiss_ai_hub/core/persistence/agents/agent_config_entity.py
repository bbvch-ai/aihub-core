from typing import Self

from mongoengine import DictField, EmbeddedDocumentField, StringField
from mongoengine.base import BaseDocument

from swiss_ai_hub.core.agents.agent_config import AgentConfig
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity


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
    config_data = DictField(required=True, description="The configuration data matching the Pydantic model.")

    @classmethod
    @trace_fn
    def from_agent_config(cls, agent_config: AgentConfig, agent_class: str) -> Self:
        """Create an instance entity from an AgentConfig."""
        return cls(
            agent_class=agent_class,
            agent_id=agent_config.agent_id,
            name=LocaleStringEntity.from_locale_string(agent_config.name),
            description=LocaleStringEntity.from_locale_string(agent_config.description),
            icon=agent_config.icon,
            config_data=agent_config.model_dump(),
        )

    @trace_fn
    def update_from_agent_config(self, agent_config: AgentConfig, agent_class: str) -> Self:
        """Update an existing instance entity from an AgentConfig."""
        self.agent_class = agent_class
        self.agent_id = agent_config.agent_id
        self.name = LocaleStringEntity.from_locale_string(agent_config.name)
        self.description = LocaleStringEntity.from_locale_string(agent_config.description)
        self.icon = agent_config.icon
        self.config_data = agent_config.model_dump()
        return self
