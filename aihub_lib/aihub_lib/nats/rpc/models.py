from typing import Annotated, Any

from pydantic import BaseModel, Field


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
