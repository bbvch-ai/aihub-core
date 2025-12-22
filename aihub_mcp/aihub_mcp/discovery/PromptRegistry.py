"""Registry for agent-specific prompt templates."""

import logging
from typing import TYPE_CHECKING, Any

from fastmcp.prompts.prompt import PromptMessage, TextContent  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from aihub_mcp.server.MCPServer import MCPServer

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Manages MCP prompts for agent interactions.

    Creates agent-specific prompt templates based on:
    - Agent capabilities (conversational, RAG, etc.)
    - Agent configuration schemas
    - Common use patterns
    """

    def __init__(self, mcp_server: "MCPServer") -> None:
        self._mcp_server = mcp_server

    def register_agent_prompts(
        self,
        agent_class: str,
        is_conversational: bool,
        agent_metadata: dict[str, Any],
    ) -> None:
        """Register prompts for a discovered agent."""
        mcp = self._mcp_server.mcp

        if is_conversational:
            self._register_chat_prompt(mcp, agent_class)

        # Register analysis prompt for all agents
        self._register_analysis_prompt(mcp, agent_class)

        logger.debug(f"Registered prompts for agent: {agent_class}")

    def _register_chat_prompt(self, mcp: Any, agent_class: str) -> None:
        """Register a chat prompt for conversational agents."""

        @mcp.prompt(name=f"chat_with_{agent_class.lower()}")  # type: ignore[untyped-decorator]
        def chat_prompt(message: str) -> PromptMessage:
            """Start a conversation with this agent."""
            text = (
                f"You are interacting with the {agent_class} agent. "
                f"Send your message to start a conversation:\n\n{message}"
            )
            return PromptMessage(role="user", content=TextContent(type="text", text=text))

    def _register_analysis_prompt(self, mcp: Any, agent_class: str) -> None:
        """Register an analysis prompt for all agents."""

        @mcp.prompt(name=f"analyze_with_{agent_class.lower()}")  # type: ignore[untyped-decorator]
        def analysis_prompt(content: str, task: str = "analyze") -> PromptMessage:
            """Use this agent to analyze content."""
            text = (
                f"Use the {agent_class} agent to {task} the following content:\n\n"
                f"---\n{content}\n---\n\n"
                f"Provide a comprehensive analysis."
            )
            return PromptMessage(role="user", content=TextContent(type="text", text=text))
