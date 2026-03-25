from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig


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
