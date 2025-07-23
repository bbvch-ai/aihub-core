from typing import Annotated, Any

from pydantic import BaseModel, Field

from aihub_lib.agents.AgentConfig import AgentConfig


class AgentConfigSpecs(BaseModel):
    """
    Defines a specification for an agent's configuration.
    """

    agent_config_schema: Annotated[
        dict[str, Any],
        Field(
            description="A dictionary describing the schema of the agent configuration, providing details about "
            "expected fields and their types. This helps external consumers understand how to "
            "construct and validate agent configurations.",
        ),
    ]

    @classmethod
    def from_agent_config_class(cls, agent_config_class: type[AgentConfig]):
        return cls(
            agent_config_schema=agent_config_class.model_json_schema(),
        )
