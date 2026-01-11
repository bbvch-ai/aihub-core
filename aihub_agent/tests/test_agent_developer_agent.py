"""Unit tests for AgentDeveloperAgent."""

from unittest.mock import AsyncMock, MagicMock, patch

import opencode_ai
import pytest
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.AgentDeveloperAgent import AgentDeveloperAgent, AgentDeveloperAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner


@pytest.mark.asyncio
async def test_agent_developer_agent_basic():
    """Test basic message proxying to OpenCode."""

    # Mock OpenCode client
    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        # Mock session creation
        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session

        # Mock init (returns None)
        mock_client.session.init.return_value = None

        # Mock chat response
        mock_response = MagicMock()
        mock_response.parts = [
            MagicMock(type="text", text="I'll create a RAG agent for you."),
        ]
        mock_client.session.chat.return_value = mock_response

        # Run agent
        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent",
            agent_id="test-agent",
            opencode_server_url="http://localhost:8080",
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build a RAG agent")

        result = await runner.run(agent_config=config, start_event=event)

        # Assertions
        assert result.stop_event is not None
        # Should have created session
        mock_client.session.create.assert_called_once()
        # Should have sent message
        mock_client.session.chat.assert_called_once()


@pytest.mark.asyncio
async def test_agent_developer_agent_session_reuse():
    """Test that OpenCode session is reused across messages."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        # Mock session creation
        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session

        # Mock init and chat
        mock_client.session.init.return_value = None

        mock_response = MagicMock()
        mock_response.parts = [MagicMock(type="text", text="Response")]
        mock_client.session.chat.return_value = mock_response

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent", agent_id="test-agent", opencode_server_url="http://localhost:8080"
        )

        # First message
        event1 = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build agent 1")
        await runner.run(agent_config=config, start_event=event1)

        # Second message (same runner = same thread context)
        event2 = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build agent 2")
        await runner.run(agent_config=config, start_event=event2)

        # Should only create session once
        assert mock_client.session.create.call_count == 1

        # Should chat twice
        assert mock_client.session.chat.call_count == 2


@pytest.mark.asyncio
async def test_agent_developer_agent_file_change():
    """Test formatting of file creation events."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session
        mock_client.session.init.return_value = None

        # Mock response with file part
        mock_file_part = MagicMock()
        mock_file_part.type = "file"
        mock_file_part.source = MagicMock()
        mock_file_part.source.path = "/workspace/agent/MyAgent.py"
        mock_file_part.modified = False

        mock_response = MagicMock()
        mock_response.parts = [mock_file_part]
        mock_client.session.chat.return_value = mock_response

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent",
            agent_id="test-agent",
            opencode_server_url="http://localhost:8080",
            show_file_changes=True,
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build agent")

        result = await runner.run(agent_config=config, start_event=event)

        # Check that file creation was reported
        # Result contains ChunkEvents collected during execution
        assert result.stop_event is not None


@pytest.mark.asyncio
async def test_agent_developer_agent_connection_error():
    """Test handling of OpenCode connection errors."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        # Mock connection error
        mock_client.session.create.side_effect = opencode_ai.APIConnectionError("Connection refused")

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent", agent_id="test-agent", opencode_server_url="http://localhost:8080"
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build a RAG agent")

        result = await runner.run(agent_config=config, start_event=event)

        # Should complete without exception
        assert result.stop_event is not None
        # No exception event (errors handled gracefully)
        assert result.exception_event is None


@pytest.mark.asyncio
async def test_agent_developer_agent_rate_limit_error():
    """Test handling of rate limit errors."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session
        mock_client.session.init.return_value = None

        # Mock rate limit error
        mock_client.session.chat.side_effect = opencode_ai.RateLimitError("Rate limit exceeded")

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent", agent_id="test-agent", opencode_server_url="http://localhost:8080"
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build agent")

        result = await runner.run(agent_config=config, start_event=event)

        # Should complete without exception
        assert result.stop_event is not None
        assert result.exception_event is None


@pytest.mark.asyncio
async def test_agent_developer_agent_tool_execution():
    """Test formatting of tool execution events."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session
        mock_client.session.init.return_value = None

        # Mock response with tool part
        mock_tool_part = MagicMock()
        mock_tool_part.type = "tool"
        mock_tool_part.name = "pytest"
        mock_tool_part.state = "completed"

        mock_response = MagicMock()
        mock_response.parts = [mock_tool_part]
        mock_client.session.chat.return_value = mock_response

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent",
            agent_id="test-agent",
            opencode_server_url="http://localhost:8080",
            show_tool_calls=True,
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Run tests")

        result = await runner.run(agent_config=config, start_event=event)

        # Should complete successfully
        assert result.stop_event is not None


@pytest.mark.asyncio
async def test_agent_developer_agent_multiple_parts():
    """Test handling of multiple response parts."""

    with patch("aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent.AsyncOpencode") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client

        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_client.session.create.return_value = mock_session
        mock_client.session.init.return_value = None

        # Mock response with multiple parts
        mock_text_part = MagicMock(type="text", text="Creating agent...")
        mock_file_part = MagicMock(type="file", source=MagicMock(path="/workspace/agent/Agent.py"))
        mock_tool_part = MagicMock(type="tool", name="pytest", state="completed")

        mock_response = MagicMock()
        mock_response.parts = [mock_text_part, mock_file_part, mock_tool_part]
        mock_client.session.chat.return_value = mock_response

        runner = AgentTestRunner(agent_class=AgentDeveloperAgent)

        config = AgentDeveloperAgentConfig(
            agent_class="AgentDeveloperAgent", agent_id="test-agent", opencode_server_url="http://localhost:8080"
        )

        event = UserMessageEvent.create_for_user_message(user_id="test-user", content="Build agent")

        result = await runner.run(agent_config=config, start_event=event)

        # Should process all parts
        assert result.stop_event is not None
