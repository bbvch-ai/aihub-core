from typing import TYPE_CHECKING, Annotated, Any, Self

from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from pydantic import Field

from aihub_api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO

from .WorkRequestDTO import WorkRequestDTO

if TYPE_CHECKING:
    from aihub_lib.i18n.LocaleHandler import LocaleHandler


class AgentWorkRequestDTO(WorkRequestDTO):
    """DTO representing an agent work request with specific agent-related information."""

    agent_class: Annotated[str, Field(description="The class of the agent that should handle this request.")]
    agent_id: Annotated[str, Field(description="The ID of the agent that should handle this request.")]
    agent_info: Annotated[
        MinimalAgentInstanceDTO | None,
        Field(description="Detailed information about the agent instance, if available."),
    ] = None
    start_event: Annotated[dict[str, Any], Field(description="The start event that will be sent to the agent.")] = {}

    @classmethod
    def from_event_data(
        cls, event_data: dict, event_id: str, event_name: str, created_at: int, t: "LocaleHandler"
    ) -> Self:
        """Creates an AgentWorkRequestDTO from raw event data."""
        # Try to get agent information from both class and config entities
        agent_class = event_data["agent_class"]
        agent_id = event_data["agent_id"]
        agent_info: MinimalAgentInstanceDTO | None = None

        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if class_entity and config_entity:
            agent_info = MinimalAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

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
            request_type="agent",
            display_name=display_name,
            display_description=display_description,
            data=event_data,
            agent_class=agent_class,
            agent_id=agent_id,
            agent_info=agent_info,
            start_event=event_data.get("start_event", {}),
        )
