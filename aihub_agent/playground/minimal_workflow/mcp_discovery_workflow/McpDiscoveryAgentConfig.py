from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.mcp.McpHostConfig import McpHostConfig
from pydantic import Field


class McpDiscoveryAgentConfig(AgentConfig):
    """Configuration for the MCP Discovery demo agent. No LLM needed."""

    mcp: Annotated[McpHostConfig, Field(description="MCP Host configuration.")]
