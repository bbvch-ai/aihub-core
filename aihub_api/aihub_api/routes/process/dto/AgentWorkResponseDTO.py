from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_lib.persistence.agents import AgentEntity

from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class AgentWorkResponseDTO(WorkResponseDTO):
    """DTO representing an agent work response with specific agent-related information."""
    agent_class: Annotated[str, Field(description="The class of the agent that should handle this request.")]
    agent_id: Annotated[str, Field(description="The ID of the agent that should handle this request.")]
    agent_info: Annotated[
        MinimalAgentDTO | None, Field(description="Detailed information about the agent, if available.")
    ] = None
    agent_stop_event: Annotated[
        dict[str, Any], Field(description="The stop event returned by the agent after completing the work.")
    ] = {}

    @classmethod
    def from_event_data(
        cls,
        event_data: dict,
        event_id: str,
        event_name: str,
        created_at: int,
        t: "LocaleHandler",
    ) -> "AgentWorkResponseDTO":
        """Creates an AgentWorkResponseDTO from raw event data."""
        # Try to get agent information
        agent_class = event_data["submitted_by"]["agent_class"]
        agent_id = event_data["submitted_by"]["agent_id"]
        agent_info: MinimalAgentDTO | None = None

        agent_entity = AgentEntity.get_agent(agent_class, agent_id)
        if agent_entity:
            agent_info = MinimalAgentDTO.from_entity(agent_entity, t)

        # Extract localized display fields
        display_name: str | None = None
        display_description: str | None = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data["display_name"])
        if event_data.get("display_description"):
            display_description = t.extract(event_data["display_description"])

        return cls(
            event_id=event_id,
            event_name=event_name,
            created_at=created_at,
            response_type="agent",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            agent_class=agent_class,
            agent_id=agent_id,
            agent_info=agent_info,
            agent_stop_event=event_data.get("agent_stop_event", {}),
        )
