from typing import TYPE_CHECKING, Annotated, Any

from pydantic import Field

from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO

from .WorkResponseDTO import WorkResponseDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class AgentWorkResponseDTO(WorkResponseDTO):
    """DTO representing an agent work response with specific agent-related information."""

    agent_info: Annotated[
        MinimalAgentDTO | None, Field(description="Detailed information about the agent, if available.")
    ]

    agent_stop_event: Annotated[
        dict[str, Any], Field(description="The stop event returned by the agent after completing the work.")
    ]

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler", agent_info: "MinimalAgentDTO | None" = None
    ) -> "AgentWorkResponseDTO":
        """Creates an AgentWorkResponseDTO from raw event data."""
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
            response_type="agent",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            agent_info=agent_info,
            agent_stop_event=event_data.get("agent_stop_event", {}),
        )
