from typing import Annotated, Any

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.discovery.event_specs import EventSpecs
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class FetchAgentConfigRequest(BaseModel):
    """Request to fetch agent configuration."""

    agent_class: Annotated[str, Field(description="Agent class name")]
    agent_id: Annotated[str, Field(description="Agent instance ID")]


class FetchAgentConfigResponse(BaseModel):
    """Response containing agent configuration."""

    agent_class: Annotated[str, Field(description="Agent class name")]
    agent_id: Annotated[str, Field(description="Agent instance ID")]
    config: Annotated[dict[str, Any], Field(description="Agent configuration values")]
    found: Annotated[bool, Field(description="Whether config was found")] = True
    error: Annotated[str | None, Field(description="Error message if failed")] = None


class FetchProcessConfigRequest(BaseModel):
    """Request to fetch process configuration."""

    process_class: Annotated[str, Field(description="Process class name")]
    process_id: Annotated[str, Field(description="Process instance ID")]


class FetchProcessConfigResponse(BaseModel):
    """Response containing process configuration."""

    process_class: Annotated[str, Field(description="Process class name")]
    process_id: Annotated[str, Field(description="Process instance ID")]
    config: Annotated[dict[str, Any], Field(description="Process configuration values")]
    found: Annotated[bool, Field(description="Whether config was found")] = True
    error: Annotated[str | None, Field(description="Error message if failed")] = None


class ListCallableAgentsRequest(BaseModel):
    """Request for the agent profiles that are online, for an agent offering them to its model as tools."""


class CallableAgent(BaseModel):
    """An online agent profile another agent may call, with what its model needs to decide whether to."""

    agent_class: Annotated[str, Field(description="Agent class name")]
    agent_id: Annotated[str, Field(description="Agent profile ID")]
    name: Annotated[LocaleString, Field(description="The profile's name")]
    description: Annotated[LocaleString, Field(description="The profile's description")]
    is_conversational: Annotated[bool, Field(description="Whether the agent starts from a chat message")]
    start_events: Annotated[list[EventSpecs], Field(description="The start events the agent accepts")] = []


class ListCallableAgentsResponse(BaseModel):
    """Every online agent profile; the asking agent narrows them to what its user may use."""

    agents: Annotated[list[CallableAgent], Field(description="Online agent profiles")] = []
