from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.agents import AgentClassEntity

from swiss_ai_hub.api.routes.agent.dto.agent_config_dto import AgentConfigDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument


class MinimalAgentInstanceDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal agent INSTANCE.
    Only contains minimal information about a specific agent instance.

    NOTE: This represents an INSTANCE (with agent_id), not an agent CLASS.
    For class-level data only, use AgentClassDTO.
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
    is_schedulable: Annotated[
        bool, Field(description="Whether the agent can be run automatically on a cron schedule")
    ] = False

    @property
    def name(self) -> str:
        """Returns agent name from config."""
        return self.agent_config.name

    @classmethod
    def from_class_and_config(
        cls,
        class_entity: AgentClassEntity,
        config_entity: "AgentConfigEntityDocument",
        t: LocaleHandler,
    ) -> Self:
        """
        Creates a MinimalAgentInstanceDTO from a class entity and a config entity.
        Class entity provides is_conversational, config entity provides instance-specific data.
        """
        agent_config_dto = AgentConfigDTO.from_class_and_config(class_entity, config_entity, t)
        return cls(
            agent_class=class_entity.agent_class,
            agent_id=config_entity.agent_id,
            agent_config=agent_config_dto,
            is_conversational=class_entity.is_conversational,
            is_schedulable=class_entity.is_schedulable,
        )
