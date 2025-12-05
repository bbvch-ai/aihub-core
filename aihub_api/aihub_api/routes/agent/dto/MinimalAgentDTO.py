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
        AgentConfigDTO | None,
        Field(description="Configuration details of the agent, including name, description, and prompts."),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]

    @property
    def name(self) -> str:
        """Returns agent name from config, or agent_id as fallback for backwards compatibility."""
        if self.agent_config is not None:
            return self.agent_config.name
        return self.agent_id

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "MinimalAgentDTO":
        """Converts an AgentEntity to a MinimalAgentDTO."""
        agent_config_dto = AgentConfigDTO.from_agent_config_entity_specs(entity.agent_config_specs, t)
        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=entity.is_conversational,
        )
