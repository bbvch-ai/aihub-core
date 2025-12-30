"""Dynamic agent to MCP tool registration."""

import json
import logging
import re
from typing import TYPE_CHECKING, Any

from fastmcp import Context

if TYPE_CHECKING:
    from aihub_mcp.server.MCPServer import MCPServer
    from aihub_mcp.translation.EventTranslator import EventTranslator

logger = logging.getLogger(__name__)

# Maximum sizes for input validation
MAX_MESSAGE_LENGTH = 100_000  # 100KB max message
MAX_JSON_DEPTH = 10  # Maximum nesting depth for JSON

# Patterns that might indicate injection attempts
SUSPICIOUS_PATTERNS = [
    re.compile(r"__proto__", re.I),
    re.compile(r"constructor\s*\[", re.I),
    re.compile(r"\$\{.*\}", re.I),  # Template injection
]


class InputValidationError(ValueError):
    """Raised when input validation fails."""

    pass


def validate_event_data(data: dict[str, Any], schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Validate event data for security issues.

    Checks:
    - Size limits
    - Dangerous patterns
    - Schema compliance (if provided)
    """
    # Convert to string to check total size
    data_str = json.dumps(data)
    if len(data_str) > MAX_MESSAGE_LENGTH:
        raise InputValidationError(f"Input too large: {len(data_str)} bytes (max {MAX_MESSAGE_LENGTH})")

    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(data_str):
            logger.warning(f"Suspicious pattern detected in input: {pattern.pattern}")
            raise InputValidationError("Input contains potentially dangerous patterns")

    # Check nesting depth
    def check_depth(obj: Any, current_depth: int = 0) -> None:
        if current_depth > MAX_JSON_DEPTH:
            raise InputValidationError(f"Input nesting too deep (max {MAX_JSON_DEPTH})")
        if isinstance(obj, dict):
            for v in obj.values():
                check_depth(v, current_depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                check_depth(item, current_depth + 1)

    check_depth(data)

    # Schema validation (if provided)
    if schema:
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})

        for field in required_fields:
            if field not in data:
                raise InputValidationError(f"Missing required field: {field}")

        for field, value in data.items():
            if field in properties:
                field_type = properties[field].get("type")
                if field_type == "string" and not isinstance(value, str):
                    raise InputValidationError(f"Field '{field}' must be a string")
                elif field_type == "number" and not isinstance(value, int | float):
                    raise InputValidationError(f"Field '{field}' must be a number")
                elif field_type == "boolean" and not isinstance(value, bool):
                    raise InputValidationError(f"Field '{field}' must be a boolean")
                elif field_type == "array" and not isinstance(value, list):
                    raise InputValidationError(f"Field '{field}' must be an array")
                elif field_type == "object" and not isinstance(value, dict):
                    raise InputValidationError(f"Field '{field}' must be an object")

    return data


def _to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


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

        For conversational agents with UserMessageEvent, creates a chat tool with proper parameters.
        For other events, creates tools with JSON input.
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

            # Register based on event type
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

            self._registered_tools[tool_name] = agent_class
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
        event_translator = self._event_translator

        @mcp.tool(name=tool_name, description=description)
        async def chat_tool(
            message: str,
            ctx: Context,
            locale: str = "en",
            conversation_history: str | None = None,
        ) -> str:
            """
            Chat with the agent.

            Args:
                message: The user's message to send to the agent.
                locale: Language locale (e.g., 'en', 'de', 'fr'). Default: 'en'.
                conversation_history: Optional JSON array of previous messages for context.
                    Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            """
            # Build messages array
            messages: list[dict[str, str]] = []

            # Add conversation history if provided
            if conversation_history:
                try:
                    history = json.loads(conversation_history)
                    if isinstance(history, list):
                        messages.extend(history)
                except json.JSONDecodeError:
                    await ctx.warning("Could not parse conversation_history as JSON, ignoring")

            # Add current message
            messages.append({"role": "user", "content": message})

            # Build event data matching UserMessageEvent schema
            event_data = {
                "locale": locale,
                "messages": messages,
                "user": {
                    "id": "mcp_client",
                    "name": "MCP Client",
                    "email": "mcp@aihub.local",
                },
            }

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
        event_translator = self._event_translator

        # Extract schema info for documentation
        properties = self._extract_input_properties(event_schema)
        required = event_schema.get("required", [])

        # Build schema documentation
        schema_doc = self._build_schema_documentation(properties, required)

        @mcp.tool(name=tool_name, description=f"{description}\n\n{schema_doc}")
        async def generic_tool(
            event_data_json: str,
            ctx: Context,
        ) -> str:
            """
            Invoke the agent with event data.

            Args:
                event_data_json: JSON object containing the event data.
                    See tool description for required and optional fields.
            """
            try:
                event_data = json.loads(event_data_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e

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
