"""Dynamic agent to MCP tool registration."""

import logging
from typing import TYPE_CHECKING, Any

from fastmcp import Context

if TYPE_CHECKING:
    from aihub_mcp.server.MCPServer import MCPServer
    from aihub_mcp.translation.EventTranslator import EventTranslator

logger = logging.getLogger(__name__)


class AgentToolRegistry:
    """
    Dynamically registers AI Hub agents as MCP tools.

    Each agent's start events become MCP tools with schemas derived from EventSpecs.
    The registry handles:
    - Converting agent event schemas to MCP tool schemas
    - Creating tool handlers that invoke agents via SAAP
    - Managing tool lifecycle as agents come online/offline
    """

    def __init__(
        self,
        mcp_server: "MCPServer",
        event_translator: "EventTranslator",
    ) -> None:
        self._mcp_server = mcp_server
        self._event_translator = event_translator
        self._registered_tools: dict[str, str] = {}  # tool_name -> agent_class

    def register_agent_tools(
        self,
        agent_class: str,
        start_events: list[dict[str, Any]],
        is_conversational: bool,
    ) -> None:
        """
        Register MCP tools for an agent based on its start events.

        For conversational agents, creates a main chat tool.
        For all agents, creates tools for each custom start event.
        """
        for event_spec in start_events:
            event_name = event_spec["event_name"]
            event_schema = event_spec["event_schema"]
            event_parents = event_spec.get("event_parents", [])

            # Generate tool name
            tool_name = self._generate_tool_name(agent_class, event_name)

            # Skip if already registered
            if tool_name in self._registered_tools:
                logger.debug(f"Tool already registered: {tool_name}")
                continue

            # Create tool description
            description = self._generate_tool_description(
                agent_class,
                event_name,
                event_schema,
                is_conversational,
            )

            # Register the tool dynamically
            self._register_tool(
                tool_name=tool_name,
                description=description,
                agent_class=agent_class,
                event_name=event_name,
                event_schema=event_schema,
                event_parents=event_parents,
            )

            self._registered_tools[tool_name] = agent_class
            logger.info(f"Registered MCP tool: {tool_name} for agent {agent_class}")

    def _generate_tool_name(self, agent_class: str, event_name: str) -> str:
        """Generate a valid MCP tool name from agent class and event name."""
        # Convert CamelCase to snake_case and combine
        import re

        def to_snake_case(name: str) -> str:
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

        agent_snake = to_snake_case(agent_class)
        event_snake = to_snake_case(event_name.replace("Event", ""))

        return f"{agent_snake}_{event_snake}"

    def _generate_tool_description(
        self,
        agent_class: str,
        event_name: str,
        event_schema: dict[str, Any],
        is_conversational: bool,
    ) -> str:
        """Generate a description for the MCP tool."""
        schema_description = event_schema.get("description", "")

        if is_conversational and "UserMessage" in event_name:
            return (
                f"Chat with the {agent_class} agent. "
                f"Send a message and receive a response. "
                f"This agent supports streaming responses and may request human input during execution. "
                f"{schema_description}"
            )

        return (
            f"Invoke the {agent_class} agent with a {event_name}. "
            f"This triggers the agent's workflow and returns the result. "
            f"{schema_description}"
        )

    def _register_tool(
        self,
        tool_name: str,
        description: str,
        agent_class: str,
        event_name: str,
        event_schema: dict[str, Any],
        event_parents: list[str],
    ) -> None:
        """Register a single MCP tool for an agent event."""
        mcp = self._mcp_server.mcp
        event_translator = self._event_translator

        # Note: event_schema could be used for more sophisticated schema validation
        # Currently we use a generic message parameter approach
        _ = event_schema  # Acknowledge the parameter for future use

        # Create the tool handler
        async def tool_handler(ctx: Context, **kwargs: Any) -> str:
            """Handle MCP tool invocation by translating to SAAP."""
            try:
                # Log progress start
                await ctx.info(f"Invoking {agent_class} agent...")

                # Execute via event translator
                result = await event_translator.execute_agent(
                    agent_class=agent_class,
                    event_name=event_name,
                    event_parents=event_parents,
                    event_data=kwargs,
                    ctx=ctx,
                )

                return result

            except Exception as e:
                error_msg = f"Agent execution failed: {e!s}"
                await ctx.error(error_msg)
                raise

        # Build parameter schema for the tool
        # FastMCP uses function signature, so we need to register with proper types
        # For dynamic registration, we use @mcp.tool with the handler

        # Note: FastMCP doesn't support fully dynamic tool registration at runtime
        # with arbitrary schemas. We register a generic tool that accepts kwargs.
        # The schema is communicated via description.

        @mcp.tool(name=tool_name, description=description)
        async def dynamic_tool(message: str, ctx: Context) -> str:
            """
            Invoke the agent with a message.

            For conversational agents, this is the user's message.
            For other agents, this should contain the required event data as JSON.
            """
            import json

            # Parse message as JSON if it looks like JSON, otherwise treat as message
            try:
                if message.strip().startswith("{"):
                    event_data = json.loads(message)
                else:
                    event_data = {"message": message}
            except json.JSONDecodeError:
                event_data = {"message": message}

            return await tool_handler(ctx, **event_data)

    def _extract_input_properties(self, event_schema: dict[str, Any]) -> dict[str, Any]:
        """Extract input properties from event JSON schema."""
        properties = event_schema.get("properties", {})

        # Filter out internal fields
        internal_fields = {"event_id", "created_at", "_event_name", "_parent_event_names"}
        return {k: v for k, v in properties.items() if k not in internal_fields}

    def unregister_agent_tools(self, agent_class: str) -> None:
        """Remove all tools for an agent that went offline."""
        tools_to_remove = [tool_name for tool_name, ac in self._registered_tools.items() if ac == agent_class]

        for tool_name in tools_to_remove:
            del self._registered_tools[tool_name]
            logger.info(f"Unregistered MCP tool: {tool_name}")

        # Note: FastMCP doesn't support runtime tool removal
        # Tools will remain registered but will fail when invoked

    def get_registered_tools(self) -> dict[str, str]:
        """Get mapping of registered tool names to agent classes."""
        return self._registered_tools.copy()
