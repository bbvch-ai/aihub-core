from datetime import datetime
from typing import Annotated, Any

from aihub_lib.persistence.agents.AgentConfigEntity import AgentConfigEntity
from pydantic import BaseModel, Field


class CreateAgentConfigInstanceRequest(BaseModel):
    """Request model for creating a new agent configuration instance."""

    config_id: Annotated[
        str, Field(description="Unique, URL-safe ID for the config (e.g., 'hr-policy-bot'). Becomes the agent_id.")
    ]
    config_name: Annotated[str, Field(description="User-friendly display name (e.g., 'HR Policy Bot').")]
    description: Annotated[str | None, Field(description="Optional description of the configuration.")] = None
    config_data: Annotated[dict[str, Any], Field(description="The configuration data matching the Pydantic model.")]


class UpdateAgentConfigInstanceRequest(BaseModel):
    """Request model for updating an existing agent configuration instance."""

    config_name: Annotated[str, Field(description="User-friendly display name (e.g., 'HR Policy Bot').")]
    description: Annotated[str | None, Field(description="Optional description of the configuration.")] = None
    config_data: Annotated[dict[str, Any], Field(description="The configuration data matching the Pydantic model.")]


class AgentConfigInstanceDTO(BaseModel):
    """Data transfer object for agent configuration instances."""

    agent_class: Annotated[str, Field(description="The agent class this configuration belongs to.")]
    config_id: Annotated[
        str, Field(description="Unique, URL-safe ID for the config (e.g., 'hr-policy-bot'). Becomes the agent_id.")
    ]
    config_name: Annotated[str, Field(description="User-friendly display name (e.g., 'HR Policy Bot').")]
    description: Annotated[str | None, Field(description="Optional description of the configuration.")] = None
    config_data: Annotated[dict[str, Any], Field(description="The configuration data matching the Pydantic model.")]
    created_at: Annotated[datetime, Field(description="When the configuration was created.")]
    updated_at: Annotated[datetime, Field(description="When the configuration was last updated.")]

    @classmethod
    def from_entity(cls, entity: AgentConfigEntity) -> "AgentConfigInstanceDTO":
        """Convert an AgentConfigEntity to a DTO."""
        return cls(
            agent_class=entity.agent_class,
            config_id=entity.config_id,
            config_name=entity.config_name,
            description=entity.description,
            config_data=entity.config_data,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
