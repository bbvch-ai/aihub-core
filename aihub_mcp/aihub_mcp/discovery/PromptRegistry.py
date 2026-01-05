import logging

from aihub_mcp.server.MCPServer import MCPServer

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Manages MCP prompts for agent interactions.

    Creates agent-specific prompt templates that help LLMs understand how to interact
    with AI Hub agents. Prompts are registered once and remain available.
    """

    def __init__(self, mcp_server: MCPServer) -> None:
        self._mcp_server = mcp_server

    def register_agent_prompts(
        self,
        agent_class: str,
        is_conversational: bool,
    ) -> None:
        """Register prompts for a discovered agent."""
        if is_conversational:
            self._register_chat_prompt(agent_class)

        self._register_analysis_prompt(agent_class)

        logger.debug(f"Registered prompts for agent: {agent_class}")

    def _register_chat_prompt(self, agent_class: str) -> None:
        """Register a chat prompt for conversational agents."""
        mcp = self._mcp_server.mcp
        prompt_name = f"chat_with_{agent_class.lower()}"

        @mcp.prompt(name=prompt_name)
        def chat_prompt(message: str) -> str:
            """Start a conversation with this AI Hub agent."""
            return (
                f"You are interacting with the {agent_class} agent from AI Hub. "
                f"Send your message to start a conversation:\n\n{message}"
            )

    def _register_analysis_prompt(self, agent_class: str) -> None:
        """Register an analysis prompt for all agents."""
        mcp = self._mcp_server.mcp
        prompt_name = f"analyze_with_{agent_class.lower()}"

        @mcp.prompt(name=prompt_name)
        def analysis_prompt(content: str, task: str = "analyze") -> str:
            """Use this AI Hub agent to analyze content."""
            return (
                f"Use the {agent_class} agent to {task} the following content:\n\n"
                f"---\n{content}\n---\n\n"
                f"Provide a comprehensive analysis."
            )
