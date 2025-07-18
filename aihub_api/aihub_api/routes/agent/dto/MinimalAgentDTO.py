import logging
from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MinimalAgentDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal agent.
    Only contains minimal information about the agent.
    """

    agent_class: Annotated[str, Field(description="The agent's class identifier (e.g., 'my_agent_class').")]
    agent_id: Annotated[str, Field(description="Unique identifier for the agent instance (e.g., 'agent_123').")]
    agent_config: Annotated[
        AgentConfig,
        Field(description="Configuration details of the agent, including name, description, and prompts."),
    ]
    is_conversational: Annotated[
        bool, Field(description="Whether the agent can participate in a chat-based conversation")
    ]

    @classmethod
    def from_entity(cls, entity: AgentEntity, t: LocaleHandler) -> "MinimalAgentDTO":
        """Converts an AgentEntity to an AgentDTO."""
        agent_config = entity.agent_config
        if agent_config is None:
            logger.debug(f"Agent {entity.agent_id} has no specific agent_config, using default_agent_config.")
            agent_config = entity.default_agent_config

        return cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            agent_config=AgentConfig.from_entity(agent_config),
            is_conversational=entity.is_conversational,
        )
