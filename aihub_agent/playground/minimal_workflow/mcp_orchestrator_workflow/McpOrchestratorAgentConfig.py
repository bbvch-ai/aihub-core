from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.mcp.McpHostConfig import McpHostConfig
from pydantic import BaseModel, Field


class DelegatedAgentToolConfig(BaseModel):
    """Exposes another agent as a virtual tool the LLM can invoke."""

    agent_id: Annotated[str, Field(description="ID of the agent to delegate to.")]
    agent_class: Annotated[str, Field(description="Class name of the agent.")]
    tool_name: Annotated[str, Field(description="Function name the LLM sees for this agent.")]
    tool_description: Annotated[str, Field(description="Description of what the agent tool does.")]
    tool_parameters_schema: Annotated[
        dict,
        Field(description="JSON Schema for the tool parameters."),
    ] = {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Query to send to the agent."}},
        "required": ["query"],
    }


class McpOrchestratorAgentConfig(AgentConfig):
    """Configuration for the MCP Orchestrator agent."""

    mcp: Annotated[McpHostConfig, Field(description="MCP Host configuration.")]
    llm: Annotated[LLMConfig, Field(description="LLM for tool-calling decisions.")]
    delegated_agents: Annotated[
        list[DelegatedAgentToolConfig],
        Field(default_factory=list, description="Agents exposed as virtual tools to the LLM."),
    ]
