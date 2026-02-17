from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.mcp.McpHostConfig import McpHostConfig
from pydantic import Field


class McpReactAgentConfig(AgentConfig):
    """Configuration for the MCP ReAct demo agent."""

    mcp: Annotated[McpHostConfig, Field(description="MCP Host configuration.")]
    llm: Annotated[LLMConfig, Field(description="LLM for tool-calling decisions.")]
