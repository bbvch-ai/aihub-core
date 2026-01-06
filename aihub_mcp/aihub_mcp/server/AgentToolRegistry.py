import json
import logging
from typing import Any

from fastmcp import Context

from aihub_mcp.server.MCPServer import MCPServer
from aihub_mcp.translation.EventTranslator import EventTranslator

logger = logging.getLogger(__name__)

MAX_MESSAGE_SIZE = 100_000  # 100KB


def validate_event_data(data: dict[str, Any]) -> None:
    """Validate event data size to prevent DoS."""
    data_str = json.dumps(data)
    if len(data_str) > MAX_MESSAGE_SIZE:
        raise ValueError(f"Input too large: {len(data_str)} bytes (max {MAX_MESSAGE_SIZE})")


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case, handling acronyms like RAG or HTTP."""
    result: list[str] = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            prev_char = name[i - 1]
            next_is_lower = i + 1 < len(name) and name[i + 1].islower()
            # Add underscore: after lowercase, or at acronym end (e.g., HTTPServer -> http_server)
            if prev_char.islower() or next_is_lower:
                result.append("_")
        result.append(char.lower())
    return "".join(result)


class AgentToolRegistry:
    """
    Dynamically registers AI Hub agents as MCP tools.

    Each agent in AI Hub defines its own start events (the entry points for triggering
    the agent's workflow). This registry translates those events into MCP tools, allowing
    MCP clients to invoke agents without knowing the underlying SAAP event structure.

    The registry generates tool schemas dynamically from event specs, so new agents or
    event types don't require code changes here. Tool handlers perform runtime availability
    checks because agents can go offline between discovery and invocation—we fail fast
    with clear errors rather than hang waiting for a response that will never come.
    """

    def __init__(
        self,
        mcp_server: MCPServer,
        event_translator: EventTranslator,
    ) -> None:
        self._mcp_server = mcp_server
        self._event_translator = event_translator

    def register_agent_tools(
        self,
        agent_class: str,
        start_events: list[dict[str, Any]],
        is_conversational: bool,
    ) -> None:
        """Register MCP tools for an agent based on its start events."""
        for event_spec in start_events:
            event_name = event_spec["event_name"]
            event_schema = event_spec["event_schema"]
            event_parents = event_spec.get("event_parents", [])

            tool_name = self._generate_tool_name(agent_class, event_name)

            description = self._generate_tool_description(
                agent_class,
                event_name,
                event_schema,
                is_conversational,
            )

            if is_conversational and "UserMessage" in event_name:
                self._register_chat_tool(
                    tool_name=tool_name,
                    description=description,
                    agent_class=agent_class,
                    event_name=event_name,
                    event_parents=event_parents,
                )
            else:
                self._register_generic_tool(
                    tool_name=tool_name,
                    description=description,
                    agent_class=agent_class,
                    event_name=event_name,
                    event_schema=event_schema,
                    event_parents=event_parents,
                )

            logger.info(f"Registered MCP tool: {tool_name} for agent {agent_class}")

    def _generate_tool_name(self, agent_class: str, event_name: str) -> str:
        """Generate a valid MCP tool name from agent class and event name."""
        agent_snake = _to_snake_case(agent_class)
        event_snake = _to_snake_case(event_name.replace("Event", ""))
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

    def _register_chat_tool(
        self,
        tool_name: str,
        description: str,
        agent_class: str,
        event_name: str,
        event_parents: list[str],
    ) -> None:
        """Register a chat tool for conversational agents with proper message parameters."""
        mcp = self._mcp_server.mcp
        mcp_server = self._mcp_server
        event_translator = self._event_translator

        @mcp.tool(name=tool_name, description=description)
        async def chat_tool(
            message: str,
            ctx: Context,
            locale: str = "en",
            conversation_history: str | None = None,
        ) -> str:
            """Chat with the agent."""
            if not mcp_server.is_agent_registered(agent_class):
                raise ValueError(f"Agent {agent_class} is no longer available")

            messages: list[dict[str, str]] = []

            if conversation_history:
                try:
                    history = json.loads(conversation_history)
                    if isinstance(history, list):
                        messages.extend(history)
                except json.JSONDecodeError:
                    await ctx.warning("Could not parse conversation_history as JSON, ignoring")

            messages.append({"role": "user", "content": message})

            event_data = {
                "locale": locale,
                "messages": messages,
                "user": {
                    "id": "mcp_client",
                    "name": "MCP Client",
                    "email": "mcp@aihub.local",
                    "roles": ["user"],
                },
            }

            validate_event_data(event_data)

            try:
                await ctx.info(f"Invoking {agent_class} agent...")
                result = await event_translator.execute_agent(
                    agent_class=agent_class,
                    event_name=event_name,
                    event_parents=event_parents,
                    event_data=event_data,
                    ctx=ctx,
                )
                return result

            except Exception as e:
                error_msg = f"Agent execution failed: {e!s}"
                await ctx.error(error_msg)
                raise

    def _register_generic_tool(
        self,
        tool_name: str,
        description: str,
        agent_class: str,
        event_name: str,
        event_schema: dict[str, Any],
        event_parents: list[str],
    ) -> None:
        """Register a generic tool that accepts JSON input for non-conversational events."""
        mcp = self._mcp_server.mcp
        mcp_server = self._mcp_server
        event_translator = self._event_translator

        properties = self._extract_input_properties(event_schema)
        required = event_schema.get("required", [])
        schema_doc = self._build_schema_documentation(properties, required)

        @mcp.tool(name=tool_name, description=f"{description}\n\n{schema_doc}")
        async def generic_tool(
            event_data_json: str,
            ctx: Context,
        ) -> str:
            """Invoke the agent with event data."""
            if not mcp_server.is_agent_registered(agent_class):
                raise ValueError(f"Agent {agent_class} is no longer available")

            try:
                event_data = json.loads(event_data_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e

            validate_event_data(event_data)

            try:
                await ctx.info(f"Invoking {agent_class} agent...")
                result = await event_translator.execute_agent(
                    agent_class=agent_class,
                    event_name=event_name,
                    event_parents=event_parents,
                    event_data=event_data,
                    ctx=ctx,
                    tool_name=tool_name,
                )
                return result

            except Exception as e:
                error_msg = f"Agent execution failed: {e!s}"
                await ctx.error(error_msg)
                raise

    def _extract_input_properties(self, event_schema: dict[str, Any]) -> dict[str, Any]:
        """Extract input properties from event JSON schema, excluding internal fields."""
        properties = event_schema.get("properties", {})
        internal_fields = {"event_id", "created_at", "_event_name", "_parent_event_names"}
        return {k: v for k, v in properties.items() if k not in internal_fields}

    def _build_schema_documentation(
        self,
        properties: dict[str, Any],
        required: list[str],
    ) -> str:
        """Build human-readable schema documentation for the tool description."""
        if not properties:
            return ""

        lines = ["**Event Schema:**"]
        for prop_name, prop_schema in properties.items():
            prop_type = prop_schema.get("type", "any")
            prop_desc = prop_schema.get("description", "")
            is_required = prop_name in required
            req_marker = " (required)" if is_required else " (optional)"

            lines.append(f"- `{prop_name}` ({prop_type}){req_marker}: {prop_desc}")

        return "\n".join(lines)
