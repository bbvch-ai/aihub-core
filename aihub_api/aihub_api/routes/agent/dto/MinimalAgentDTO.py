from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import BaseModel, Field

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO


class MinimalAgentDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal agent.
    Only contains minimal information about the agent.
    """

    agent_class: Annotated[str, Field(description="The agent's class identifier (e.g., 'my_agent_class').")]
    agent_id: Annotated[str, Field(description="Unique identifier for the agent instance (e.g., 'agent_123').")]
    agent_config: Annotated[
        AgentConfigDTO,
        Field(description="Configuration details of the agent, including name, description, and prompts."),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]

    @property
    def name(self) -> str:
        """Returns agent name from config."""
        return self.agent_config.name

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "MinimalAgentDTO":
        """Converts an AgentEntity to a MinimalAgentDTO."""
        # Use agent_config_specs if available, otherwise fall back to default_agent_config
        agent_config_dto = AgentConfigDTO.from_agent_config_entity_specs(entity.agent_config_specs, t)
        if agent_config_dto is None:
            agent_config_dto = AgentConfigDTO.from_default_agent_config_entity(entity.default_agent_config, t)
        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=entity.is_conversational,
        )
