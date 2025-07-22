from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO

from .WorkRequestDTO import WorkRequestDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class AgentWorkRequestDTO(WorkRequestDTO):
    """DTO representing an agent work request with specific agent-related information."""

    agent_class: Annotated[str, Field(description="The class of the agent that should handle this request.")]

    agent_id: Annotated[str, Field(description="The ID of the agent that should handle this request.")]

    agent_info: Annotated[
        MinimalAgentDTO | None, Field(description="Detailed information about the agent, if available.")
    ]

    start_event: Annotated[dict[str, Any], Field(description="The start event that will be sent to the agent.")]

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> "AgentWorkRequestDTO":
        """Creates an AgentWorkRequestDTO from raw event data."""
        from aihub_lib.persistence.agents.AgentEntity import AgentEntity

        from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO

        # Try to get agent information
        agent_info = None
        agent_class = event_data.get("agent_class")
        agent_id = event_data.get("agent_id")
        if agent_class and agent_id:
            try:
                agent_entity = AgentEntity.get_agent(agent_class, agent_id)
                if agent_entity:
                    agent_info = MinimalAgentDTO.from_entity(agent_entity, t)
            except Exception:
                pass  # Agent not found or error loading

        # Extract localized display fields
        display_name = None
        display_description = None
        if event_data.get("display_name"):
            display_name = t.extract(event_data.get("display_name"))
        if event_data.get("display_description"):
            display_description = t.extract(event_data.get("display_description"))

        return cls(
            event_id=event_id,
            event_name=event_name,
            created_at=created_at,
            request_type="agent",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            agent_class=agent_class or "",
            agent_id=agent_id or "",
            agent_info=agent_info,
            start_event=event_data.get("start_event", {}),
        )
