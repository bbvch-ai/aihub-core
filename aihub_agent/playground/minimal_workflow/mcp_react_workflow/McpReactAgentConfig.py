from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events.form.constraints import Gt
from pydantic import Field


class McpReactAgentConfig(AgentConfig):
    mcp: Annotated[
        McpClientConfig,
        Field(description="MCP connection configuration for external tool servers."),
    ]
    llm: Annotated[
        LLMConfig,
        Field(description="LLM used for reasoning and tool selection."),
    ]
    max_iterations: Annotated[
        int,
        Field(default=50, description="Maximum number of reasoning iterations before graceful termination."),
        Gt(0),
    ]
