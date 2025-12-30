"""Tests for agent tool registry."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from aihub_mcp.server.AgentToolRegistry import AgentToolRegistry, _to_snake_case


class TestToSnakeCase:
    """Tests for snake_case conversion helper."""

    def test_simple_camel_case(self) -> None:
        """Test converting simple CamelCase."""
        assert _to_snake_case("RAGAgent") == "rag_agent"

    def test_acronym_handling(self) -> None:
        """Test handling of acronyms."""
        assert _to_snake_case("HTTPServer") == "http_server"
        assert _to_snake_case("XMLParser") == "xml_parser"

    def test_mixed_case(self) -> None:
        """Test mixed case patterns."""
        assert _to_snake_case("UserMessageEvent") == "user_message_event"
        assert _to_snake_case("HumanInTheLoop") == "human_in_the_loop"

    def test_already_snake_case(self) -> None:
        """Test that snake_case stays unchanged."""
        assert _to_snake_case("already_snake") == "already_snake"

    def test_single_word(self) -> None:
        """Test single word conversion."""
        assert _to_snake_case("Agent") == "agent"


class TestAgentToolRegistry:
    """Tests for AgentToolRegistry class."""

    @pytest.fixture
    def mock_mcp_server(self) -> MagicMock:
        """Create a mock MCP server."""
        server = MagicMock()
        server.mcp = MagicMock()
        server.mcp.tool = MagicMock(return_value=lambda f: f)
        return server

    @pytest.fixture
    def mock_event_translator(self) -> MagicMock:
        """Create a mock event translator."""
        translator = MagicMock()
        translator.execute_agent = AsyncMock(return_value="Test result")
        return translator

    @pytest.fixture
    def registry(self, mock_mcp_server: MagicMock, mock_event_translator: MagicMock) -> AgentToolRegistry:
        """Create a registry for testing."""
        return AgentToolRegistry(
            mcp_server=mock_mcp_server,
            event_translator=mock_event_translator,
        )

    def test_generate_tool_name(self, registry: AgentToolRegistry) -> None:
        """Test tool name generation from agent class and event."""
        name = registry._generate_tool_name("RAGAgent", "UserMessageEvent")
        assert name == "rag_agent_user_message"

    def test_generate_tool_name_removes_event_suffix(self, registry: AgentToolRegistry) -> None:
        """Test that Event suffix is removed from tool name."""
        name = registry._generate_tool_name("ChatAgent", "StartEvent")
        assert name == "chat_agent_start"

    def test_generate_tool_description_conversational(self, registry: AgentToolRegistry) -> None:
        """Test description for conversational agent."""
        description = registry._generate_tool_description(
            agent_class="ChatAgent",
            event_name="UserMessageEvent",
            event_schema={"description": "Handles user chat."},
            is_conversational=True,
        )

        assert "Chat with the ChatAgent agent" in description
        assert "streaming responses" in description
        assert "Handles user chat" in description

    def test_generate_tool_description_non_conversational(self, registry: AgentToolRegistry) -> None:
        """Test description for non-conversational agent."""
        description = registry._generate_tool_description(
            agent_class="RAGAgent",
            event_name="StartEvent",
            event_schema={"description": "Starts the RAG workflow."},
            is_conversational=False,
        )

        assert "Invoke the RAGAgent agent" in description
        assert "StartEvent" in description
        assert "Starts the RAG workflow" in description

    def test_extract_input_properties(self, registry: AgentToolRegistry) -> None:
        """Test extracting input properties from event schema."""
        schema = {
            "properties": {
                "messages": {"type": "array", "description": "Chat messages"},
                "locale": {"type": "string", "description": "Language locale"},
                "event_id": {"type": "string"},
                "created_at": {"type": "integer"},
                "_event_name": {"type": "string"},
            }
        }

        properties = registry._extract_input_properties(schema)

        # Internal fields should be excluded
        assert "messages" in properties
        assert "locale" in properties
        assert "event_id" not in properties
        assert "created_at" not in properties
        assert "_event_name" not in properties

    def test_extract_input_properties_empty(self, registry: AgentToolRegistry) -> None:
        """Test extracting from schema with no properties."""
        properties = registry._extract_input_properties({})
        assert properties == {}

    def test_build_schema_documentation(self, registry: AgentToolRegistry) -> None:
        """Test building schema documentation string."""
        properties = {
            "query": {"type": "string", "description": "The search query"},
            "limit": {"type": "integer", "description": "Max results"},
        }
        required = ["query"]

        doc = registry._build_schema_documentation(properties, required)

        assert "**Event Schema:**" in doc
        assert "`query` (string) (required)" in doc
        assert "`limit` (integer) (optional)" in doc
        assert "The search query" in doc

    def test_build_schema_documentation_empty(self, registry: AgentToolRegistry) -> None:
        """Test building schema documentation with no properties."""
        doc = registry._build_schema_documentation({}, [])
        assert doc == ""

    def test_register_agent_tools_adds_to_registry(self, registry: AgentToolRegistry) -> None:
        """Test that registering tools adds them to internal registry."""
        start_events = [
            {
                "event_name": "StartEvent",
                "event_schema": {"properties": {}},
                "event_parents": ["BaseEvent", "ControlEvent"],
            }
        ]

        registry.register_agent_tools(
            agent_class="TestAgent",
            start_events=start_events,
            is_conversational=False,
        )

        registered = registry.get_registered_tools()
        assert "test_agent_start" in registered
        assert registered["test_agent_start"] == "TestAgent"

    def test_register_skips_duplicate_tools(self, registry: AgentToolRegistry) -> None:
        """Test that duplicate tools are not re-registered."""
        start_events = [
            {
                "event_name": "StartEvent",
                "event_schema": {},
                "event_parents": [],
            }
        ]

        # Register twice
        registry.register_agent_tools("TestAgent", start_events, False)
        registry.register_agent_tools("TestAgent", start_events, False)

        # Should only have one entry
        registered = registry.get_registered_tools()
        assert len(registered) == 1

    def test_unregister_agent_tools(self, registry: AgentToolRegistry) -> None:
        """Test unregistering tools for an agent."""
        start_events = [
            {"event_name": "StartEvent", "event_schema": {}, "event_parents": []},
            {"event_name": "AnotherEvent", "event_schema": {}, "event_parents": []},
        ]

        registry.register_agent_tools("TestAgent", start_events, False)
        assert len(registry.get_registered_tools()) == 2

        registry.unregister_agent_tools("TestAgent")
        assert len(registry.get_registered_tools()) == 0

    def test_unregister_only_affects_specified_agent(self, registry: AgentToolRegistry) -> None:
        """Test that unregistering only removes tools for specified agent."""
        registry.register_agent_tools(
            "Agent1",
            [{"event_name": "StartEvent", "event_schema": {}, "event_parents": []}],
            False,
        )
        registry.register_agent_tools(
            "Agent2",
            [{"event_name": "StartEvent", "event_schema": {}, "event_parents": []}],
            False,
        )

        registry.unregister_agent_tools("Agent1")

        registered = registry.get_registered_tools()
        assert len(registered) == 1
        assert "agent2_start" in registered
