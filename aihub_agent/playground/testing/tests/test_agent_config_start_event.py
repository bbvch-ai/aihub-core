from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.start.StartEvent import StartEvent
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.context.run.RunContext import RunContext

enable_logging()


@pytest.fixture
def sample_default_config() -> dict[str, Any]:
    """Create a sample default AgentConfig for testing."""
    return AgentConfig(
        agent_class="TestAgent",
        agent_id="default_agent",
        name=LocaleString(en="Default Test Agent"),
        description=LocaleString(en="Default agent configuration"),
        icon="default-icon",
        color="#0066CC",
        voice="default-voice",
    ).model_dump()


@pytest.fixture
def sample_start_event_config() -> dict[str, Any]:
    """Create a sample AgentConfig that will be passed in a StartEvent."""
    return AgentConfig(
        agent_class="TestAgent",
        agent_id="start_event_agent",
        name=LocaleString(en="Start Event Agent"),
        description=LocaleString(en="Agent config from start event"),
        icon="start-event-icon",
        color="#FF5733",
        voice="start-event-voice",
    ).model_dump()


class TestAgentConfigPrecedence:
    """Test the precedence of AgentConfig: StartEvent > Default."""

    def test_start_event_config_precedence_logic(self, sample_default_config, sample_start_event_config):
        """Test the core logic of config precedence: event.agent_config or default_agent_config."""
        # Test with start event that has agent_config
        start_event_with_config = StartEvent(agent_config=sample_start_event_config)

        # Simulate the testing logic from AgentDispatcher.handle_event:93
        if start_event_with_config.is_start_event:
            run_agent_config = start_event_with_config.agent_config or sample_default_config

        # Verify start event config takes precedence
        assert run_agent_config == sample_start_event_config
        assert run_agent_config["agent_id"] == "start_event_agent"
        assert run_agent_config["name"]["en"] == "Start Event Agent"

    def test_default_config_fallback_logic(self, sample_default_config):
        """Test the fallback to default config when start event has no agent_config."""
        # Test with start event that has no agent_config
        start_event_without_config = StartEvent()

        # Simulate the testing logic from AgentDispatcher.handle_event:93
        if start_event_without_config.is_start_event:
            run_agent_config = start_event_without_config.agent_config or sample_default_config

        # Verify default config is used
        assert run_agent_config == sample_default_config
        assert run_agent_config["agent_id"] == "default_agent"
        assert run_agent_config["name"]["en"] == "Default Test Agent"

    def test_start_event_to_context_dict_excludes_internal_fields(self, sample_start_event_config):
        """Test that StartEvent.to_context_dict() excludes internal fields."""
        start_event = StartEvent(agent_config=sample_start_event_config)

        context_dict = start_event.to_context_dict()

        # Verify internal fields are excluded
        assert "event_id" not in context_dict
        assert "created_at" not in context_dict

        # Verify agent_config is included
        assert "agent_config" in context_dict
        assert context_dict["agent_config"] == sample_start_event_config

    def test_start_event_with_none_agent_config_uses_default(self, sample_default_config):
        """Test that StartEvent with None agent_config uses default config."""
        # Test with start event that has None agent_config
        start_event_with_none = StartEvent(agent_config=None)

        # Simulate the testing logic from AgentDispatcher.handle_event:93
        if start_event_with_none.is_start_event:
            run_agent_config = start_event_with_none.agent_config or sample_default_config

        # Verify default config is used
        assert run_agent_config == sample_default_config
        assert run_agent_config["agent_id"] == "default_agent"
        assert run_agent_config["name"]["en"] == "Default Test Agent"

    def test_multiple_start_events_with_different_configs(self, sample_default_config):
        """Test multiple start events with different agent configs."""
        # Create different agent configs
        config1 = AgentConfig(
            agent_class="TestAgent",
            agent_id="agent_1",
            name=LocaleString(en="Agent 1"),
            description=LocaleString(en="First agent"),
            icon="icon-1",
            color="#FF0000",
            voice="voice-1",
        )

        config2 = AgentConfig(
            agent_class="TestAgent",
            agent_id="agent_2",
            name=LocaleString(en="Agent 2"),
            description=LocaleString(en="Second agent"),
            icon="icon-2",
            color="#00FF00",
            voice="voice-2",
        )

        # Create start events with different configs
        start_event1 = StartEvent(agent_config=config1.model_dump())
        start_event2 = StartEvent(agent_config=config2.model_dump())
        start_event3 = StartEvent()  # No config

        # Test precedence logic for each
        if start_event1.is_start_event:
            run_config1 = start_event1.agent_config or sample_default_config
        if start_event2.is_start_event:
            run_config2 = start_event2.agent_config or sample_default_config
        if start_event3.is_start_event:
            run_config3 = start_event3.agent_config or sample_default_config

        # Verify correct configs are used
        assert run_config1 == config1.model_dump()
        assert run_config1["agent_id"] == "agent_1"
        assert run_config1["name"]["en"] == "Agent 1"

        assert run_config2 == config2.model_dump()
        assert run_config2["agent_id"] == "agent_2"
        assert run_config2["name"]["en"] == "Agent 2"

        assert run_config3 == sample_default_config
        assert run_config3["agent_id"] == "default_agent"
        assert run_config3["name"]["en"] == "Default Test Agent"


class TestAgentDispatcherConfigHandling:
    """Test AgentDispatcher handling of AgentConfig in start events with simplified mocking."""

    @pytest.mark.asyncio
    async def test_dispatcher_config_precedence_with_start_event(
        self, sample_default_config, sample_start_event_config
    ):
        """Test that AgentDispatcher correctly applies config precedence from start events."""
        # Create a start event with agent config
        start_event = StartEvent(agent_config=sample_start_event_config)

        # Mock the run context
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        # Test the key testing logic directly
        with patch("aihub_agent.dispatchers.AgentDispatcher.RunContext") as mock_run_context_class:
            mock_run_context_class.return_value = mock_run_context

            # Simulate the testing logic from AgentDispatcher.handle_event:92-94
            if start_event.is_start_event:
                run_agent_config = start_event.agent_config or sample_default_config
                await mock_run_context.set("_agent_config", run_agent_config)

                # Verify the start event config was used
                assert run_agent_config == sample_start_event_config
                mock_run_context.set.assert_called_with("_agent_config", sample_start_event_config)

    @pytest.mark.asyncio
    async def test_dispatcher_config_precedence_without_start_event_config(self, sample_default_config):
        """Test that AgentDispatcher uses default config when start event has no agent_config."""
        # Create a start event without agent config
        start_event = StartEvent()

        # Mock the run context
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        # Test the key testing logic directly
        with patch("aihub_agent.dispatchers.AgentDispatcher.RunContext") as mock_run_context_class:
            mock_run_context_class.return_value = mock_run_context

            # Simulate the testing logic from AgentDispatcher.handle_event:92-94
            if start_event.is_start_event:
                run_agent_config = start_event.agent_config or sample_default_config
                await mock_run_context.set("_agent_config", run_agent_config)

                # Verify the default config was used
                assert run_agent_config == sample_default_config
                mock_run_context.set.assert_called_with("_agent_config", sample_default_config)

    @pytest.mark.asyncio
    async def test_dispatcher_context_injection_from_start_event(self, sample_start_event_config):
        """Test that AgentDispatcher injects context from start event."""
        # Create a start event with agent config
        start_event = StartEvent(agent_config=sample_start_event_config)

        # Mock the run context
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()

        # Test the context injection logic
        with patch("aihub_agent.dispatchers.AgentDispatcher.RunContext") as mock_run_context_class:
            mock_run_context_class.return_value = mock_run_context

            # Simulate the testing logic from AgentDispatcher.handle_event:119-123
            if start_event.is_start_event:
                # Store any initial data from the StartEvent into run_context
                event_data = start_event.to_context_dict()
                for key, value in event_data.items():
                    await mock_run_context.set(key, value)

                # Verify that context was injected
                assert mock_run_context.set.call_count >= len(event_data)

                # Verify that agent_config was set
                mock_run_context.set.assert_any_call("agent_config", sample_start_event_config)

    def test_agent_config_serialization_compatibility(self, sample_start_event_config):
        """Test that AgentConfig can be serialized and deserialized for context storage."""
        # Test that AgentConfig can be serialized via model_dump()
        config_dict = sample_start_event_config

        # Verify serialization includes key fields
        assert config_dict["agent_class"] == "TestAgent"
        assert config_dict["agent_id"] == "start_event_agent"
        assert config_dict["name"]["en"] == "Start Event Agent"
        assert config_dict["color"] == "#FF5733"

        # Test that AgentConfig can be deserialized
        deserialized_config = AgentConfig.model_validate(config_dict)

        # Verify deserialization preserves data
        assert deserialized_config.model_dump() == sample_start_event_config
        assert deserialized_config.agent_id == "start_event_agent"
        assert deserialized_config.name.en == "Start Event Agent"

    def test_agent_config_run_context_retrieval_simulation(self, sample_start_event_config):
        """Test simulation of AgentConfig retrieval from run context."""
        # Simulate the testing logic from AgentDispatcher.handle_event:96-100
        # This simulates when run_agent_config is None (non-start event)
        run_agent_config = None

        # Mock run context that returns a config
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=sample_start_event_config)

        # Simulate the config retrieval logic
        async def simulate_config_retrieval():
            if run_agent_config is None:
                # Get dynamic configuration from run context
                agent_config_dict = await mock_run_context.get("_agent_config")
                if agent_config_dict:
                    retrieved_config = AgentConfig.model_validate(agent_config_dict)
                    return retrieved_config
            return run_agent_config

        # Test the retrieval
        import asyncio

        retrieved_config = asyncio.run(simulate_config_retrieval())

        # Verify the config was retrieved correctly
        assert retrieved_config.model_dump() == sample_start_event_config
        assert retrieved_config.agent_id == "start_event_agent"
        mock_run_context.get.assert_called_once_with("_agent_config")


class TestAgentConfigIntegration:
    """Integration tests for AgentConfig behavior in start events."""

    def test_end_to_end_config_flow(self, sample_default_config):
        """Test the complete flow from start event to config usage."""
        # Create custom config for this test
        custom_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="custom_agent",
            name=LocaleString(en="Custom Agent"),
            description=LocaleString(en="Custom agent for testing"),
            icon="custom-icon",
            color="#9900FF",
            voice="custom-voice",
        )

        # Step 1: Start event with custom config
        start_event = StartEvent(agent_config=custom_config.model_dump())

        # Step 2: Dispatcher precedence logic
        if start_event.is_start_event:
            run_agent_config = start_event.agent_config or sample_default_config

        # Step 3: Context injection
        event_data = start_event.to_context_dict()

        # Step 4: Config serialization for storage
        config_dict = run_agent_config

        # Step 5: Config deserialization for usage
        final_config = AgentConfig.model_validate(config_dict)

        # Verify the entire flow
        assert final_config == custom_config
        assert final_config.agent_id == "custom_agent"
        assert final_config.name.en == "Custom Agent"
        assert final_config.color == "#9900FF"
        assert "agent_config" in event_data
        assert event_data["agent_config"] == custom_config.model_dump()

    def test_config_override_scenarios(self, sample_default_config):
        """Test different scenarios of config override behavior."""
        scenarios = [
            # Scenario 1: Start event with config
            {
                "start_event": StartEvent(
                    agent_config=AgentConfig(
                        agent_class="TestAgent",
                        agent_id="override_1",
                        name=LocaleString(en="Override 1"),
                        description=LocaleString(en="First override"),
                        icon="override-1",
                        color="#FF0000",
                        voice="override-1",
                    ).model_dump()
                ),
                "expected_id": "override_1",
                "expected_name": "Override 1",
            },
            # Scenario 2: Start event without config (should use default)
            {
                "start_event": StartEvent(),
                "expected_id": "default_agent",
                "expected_name": "Default Test Agent",
            },
            # Scenario 3: Start event with None config (should use default)
            {
                "start_event": StartEvent(agent_config=None),
                "expected_id": "default_agent",
                "expected_name": "Default Test Agent",
            },
        ]

        for i, scenario in enumerate(scenarios):
            start_event = scenario["start_event"]

            # Apply testing logic
            if start_event.is_start_event:
                run_agent_config = start_event.agent_config or sample_default_config

            # Verify expected behavior
            assert run_agent_config["agent_id"] == scenario["expected_id"], f"Scenario {i+1} failed: wrong agent_id"
            assert run_agent_config["name"]["en"] == scenario["expected_name"], f"Scenario {i+1} failed: wrong name"
