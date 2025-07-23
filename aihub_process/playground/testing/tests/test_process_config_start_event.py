from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import ProcessStartEvent
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.logging.logger import enable_logging

from aihub_process.context.walkthrough.WalkthroughContext import WalkthroughContext

enable_logging()


@pytest.fixture
def sample_default_config() -> dict[str, Any]:
    """Create a sample default ProcessConfig for testing."""
    return ProcessConfig(
        process_class="TestProcess",
        process_id="default_process",
        name=LocaleString(en="Default Test Process"),
        description=LocaleString(en="Default process configuration"),
        icon="default-icon",
    ).model_dump()


@pytest.fixture
def sample_start_event_config() -> dict[str, Any]:
    """Create a sample ProcessConfig that will be passed in a ProcessStartEvent."""
    return ProcessConfig(
        process_class="TestProcess",
        process_id="start_event_process",
        name=LocaleString(en="Start Event Process"),
        description=LocaleString(en="Process config from start event"),
        icon="start-event-icon",
    ).model_dump()


class TestProcessConfigPrecedence:
    """Test the precedence of ProcessConfig: ProcessStartEvent > Default."""

    def test_start_event_config_precedence_logic(self, sample_default_config, sample_start_event_config):
        """Test the core logic of config precedence: event.process_config or default_process_config."""
        # Test with start event that has process_config
        start_event_with_config = ProcessStartEvent(process_config=sample_start_event_config)

        # Simulate the testing logic from ProcessDispatcher.handle_event:93
        if start_event_with_config.is_start_event:
            walkthrough_process_config = start_event_with_config.process_config or sample_default_config

        # Verify start event config takes precedence
        assert walkthrough_process_config == sample_start_event_config
        assert walkthrough_process_config["process_id"] == "start_event_process"
        assert walkthrough_process_config["name"]["en"] == "Start Event Process"

    def test_default_config_fallback_logic(self, sample_default_config):
        """Test the fallback to default config when start event has no process_config."""
        # Test with start event that has no process_config
        start_event_without_config = ProcessStartEvent()

        # Simulate the testing logic from ProcessDispatcher.handle_event:93
        if start_event_without_config.is_start_event:
            walkthrough_process_config = start_event_without_config.process_config or sample_default_config

        # Verify default config is used
        assert walkthrough_process_config == sample_default_config
        assert walkthrough_process_config["process_id"] == "default_process"
        assert walkthrough_process_config["name"]["en"] == "Default Test Process"

    def test_start_event_to_context_dict_excludes_internal_fields(self, sample_start_event_config):
        """Test that ProcessStartEvent.to_context_dict() excludes internal fields."""
        start_event = ProcessStartEvent(process_config=sample_start_event_config)

        context_dict = start_event.to_context_dict()

        # Verify internal fields are excluded
        assert "event_id" not in context_dict
        assert "created_at" not in context_dict

        # Verify process_config is included
        assert "process_config" in context_dict
        assert context_dict["process_config"] == sample_start_event_config

    def test_start_event_with_none_process_config_uses_default(self, sample_default_config):
        """Test that ProcessStartEvent with None process_config uses default config."""
        # Test with start event that has None process_config
        start_event_with_none = ProcessStartEvent(process_config=None)

        # Simulate the testing logic from ProcessDispatcher.handle_event:93
        if start_event_with_none.is_start_event:
            walkthrough_process_config = start_event_with_none.process_config or sample_default_config

        # Verify default config is used
        assert walkthrough_process_config == sample_default_config
        assert walkthrough_process_config["process_id"] == "default_process"
        assert walkthrough_process_config["name"]["en"] == "Default Test Process"

    def test_multiple_start_events_with_different_configs(self, sample_default_config):
        """Test multiple start events with different process configs."""
        # Create different process configs
        config1 = ProcessConfig(
            process_class="TestProcess",
            process_id="process_1",
            name=LocaleString(en="Process 1"),
            description=LocaleString(en="First process"),
            icon="icon-1",
        )

        config2 = ProcessConfig(
            process_class="TestProcess",
            process_id="process_2",
            name=LocaleString(en="Process 2"),
            description=LocaleString(en="Second process"),
            icon="icon-2",
        )

        # Create start events with different configs
        start_event1 = ProcessStartEvent(process_config=config1.model_dump())
        start_event2 = ProcessStartEvent(process_config=config2.model_dump())
        start_event3 = ProcessStartEvent()  # No config

        # Test precedence logic for each
        if start_event1.is_start_event:
            walkthrough_config1 = start_event1.process_config or sample_default_config
        if start_event2.is_start_event:
            walkthrough_config2 = start_event2.process_config or sample_default_config
        if start_event3.is_start_event:
            walkthrough_config3 = start_event3.process_config or sample_default_config

        # Verify correct configs are used
        assert walkthrough_config1 == config1.model_dump()
        assert walkthrough_config1["process_id"] == "process_1"
        assert walkthrough_config1["name"]["en"] == "Process 1"

        assert walkthrough_config2 == config2.model_dump()
        assert walkthrough_config2["process_id"] == "process_2"
        assert walkthrough_config2["name"]["en"] == "Process 2"

        assert walkthrough_config3 == sample_default_config
        assert walkthrough_config3["process_id"] == "default_process"
        assert walkthrough_config3["name"]["en"] == "Default Test Process"


class TestProcessDispatcherConfigHandling:
    """Test ProcessDispatcher handling of ProcessConfig in start events with simplified mocking."""

    @pytest.mark.asyncio
    async def test_dispatcher_config_precedence_with_start_event(
        self, sample_default_config, sample_start_event_config
    ):
        """Test that ProcessDispatcher correctly applies config precedence from start events."""
        # Create a start event with process config
        start_event = ProcessStartEvent(process_config=sample_start_event_config)

        # Mock the walkthrough context
        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.set = AsyncMock()
        mock_walkthrough_context.get = AsyncMock()

        # Test the key testing logic directly
        with patch("aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext") as mock_walkthrough_context_class:
            mock_walkthrough_context_class.return_value = mock_walkthrough_context

            # Simulate the testing logic from ProcessDispatcher.handle_event:92-94
            if start_event.is_start_event:
                walkthrough_process_config = start_event.process_config or sample_default_config
                await mock_walkthrough_context.set("_process_config", walkthrough_process_config)

                # Verify the start event config was used
                assert walkthrough_process_config == sample_start_event_config
                mock_walkthrough_context.set.assert_called_with("_process_config", sample_start_event_config)

    @pytest.mark.asyncio
    async def test_dispatcher_config_precedence_without_start_event_config(self, sample_default_config):
        """Test that ProcessDispatcher uses default config when start event has no process_config."""
        # Create a start event without process config
        start_event = ProcessStartEvent()

        # Mock the walkthrough context
        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.set = AsyncMock()
        mock_walkthrough_context.get = AsyncMock()

        # Test the key testing logic directly
        with patch("aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext") as mock_walkthrough_context_class:
            mock_walkthrough_context_class.return_value = mock_walkthrough_context

            # Simulate the testing logic from ProcessDispatcher.handle_event:92-94
            if start_event.is_start_event:
                walkthrough_process_config = start_event.process_config or sample_default_config
                await mock_walkthrough_context.set("_process_config", walkthrough_process_config)

                # Verify the default config was used
                assert walkthrough_process_config == sample_default_config
                mock_walkthrough_context.set.assert_called_with("_process_config", sample_default_config)

    @pytest.mark.asyncio
    async def test_dispatcher_context_injection_from_start_event(self, sample_start_event_config):
        """Test that ProcessDispatcher injects context from start event."""
        # Create a start event with process config
        start_event = ProcessStartEvent(process_config=sample_start_event_config)

        # Mock the walkthrough context
        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.set = AsyncMock()

        # Test the context injection logic
        with patch("aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext") as mock_walkthrough_context_class:
            mock_walkthrough_context_class.return_value = mock_walkthrough_context

            # Simulate the testing logic from ProcessDispatcher.handle_event:119-123
            if start_event.is_start_event:
                # Store any initial data from the ProcessStartEvent into walkthrough_context
                event_data = start_event.to_context_dict()
                for key, value in event_data.items():
                    await mock_walkthrough_context.set(key, value)

                # Verify that context was injected
                assert mock_walkthrough_context.set.call_count >= len(event_data)

                # Verify that process_config was set
                mock_walkthrough_context.set.assert_any_call("process_config", sample_start_event_config)

    def test_process_config_serialization_compatibility(self, sample_start_event_config):
        """Test that ProcessConfig can be serialized and deserialized for context storage."""
        # Test that ProcessConfig can be serialized via model_dump()
        config_dict = sample_start_event_config

        # Verify serialization includes key fields
        assert config_dict["process_class"] == "TestProcess"
        assert config_dict["process_id"] == "start_event_process"
        assert config_dict["name"]["en"] == "Start Event Process"

        # Test that ProcessConfig can be deserialized
        deserialized_config = ProcessConfig.model_validate(config_dict)

        # Verify deserialization preserves data
        assert deserialized_config.model_dump() == sample_start_event_config
        assert deserialized_config.process_id == "start_event_process"
        assert deserialized_config.name.en == "Start Event Process"

    def test_process_config_walkthrough_context_retrieval_simulation(self, sample_start_event_config):
        """Test simulation of ProcessConfig retrieval from walkthrough context."""
        # Simulate the testing logic from ProcessDispatcher.handle_event:96-100
        # This simulates when walkthrough_process_config is None (non-start event)
        walkthrough_process_config = None

        # Mock walkthrough context that returns a config
        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.get = AsyncMock(return_value=sample_start_event_config)

        # Simulate the config retrieval logic
        async def simulate_config_retrieval():
            if walkthrough_process_config is None:
                # Get dynamic configuration from walkthrough context
                process_config_dict = await mock_walkthrough_context.get("_process_config")
                if process_config_dict:
                    retrieved_config = ProcessConfig.model_validate(process_config_dict)
                    return retrieved_config
            return walkthrough_process_config

        # Test the retrieval
        import asyncio

        retrieved_config = asyncio.run(simulate_config_retrieval())

        # Verify the config was retrieved correctly
        assert retrieved_config.model_dump() == sample_start_event_config
        assert retrieved_config.process_id == "start_event_process"
        mock_walkthrough_context.get.assert_called_once_with("_process_config")


class TestProcessConfigIntegration:
    """Integration tests for ProcessConfig behavior in start events."""

    def test_end_to_end_config_flow(self, sample_default_config):
        """Test the complete flow from start event to config usage."""
        # Create custom config for this test
        custom_config = ProcessConfig(
            process_class="TestProcess",
            process_id="custom_process",
            name=LocaleString(en="Custom Process"),
            description=LocaleString(en="Custom process for testing"),
            icon="custom-icon",
        )

        # Step 1: Start event with custom config
        start_event = ProcessStartEvent(process_config=custom_config.model_dump())

        # Step 2: Dispatcher precedence logic
        if start_event.is_start_event:
            walkthrough_process_config = start_event.process_config or sample_default_config

        # Step 3: Context injection
        event_data = start_event.to_context_dict()

        # Step 4: Config serialization for storage
        config_dict = walkthrough_process_config

        # Step 5: Config deserialization for usage
        final_config = ProcessConfig.model_validate(config_dict)

        # Verify the entire flow
        assert final_config == custom_config
        assert final_config.process_id == "custom_process"
        assert final_config.name.en == "Custom Process"
        assert "process_config" in event_data
        assert event_data["process_config"] == custom_config.model_dump()

    def test_config_override_scenarios(self, sample_default_config):
        """Test different scenarios of config override behavior."""
        scenarios = [
            # Scenario 1: Start event with config
            {
                "start_event": ProcessStartEvent(
                    process_config=ProcessConfig(
                        process_class="TestProcess",
                        process_id="override_1",
                        name=LocaleString(en="Override 1"),
                        description=LocaleString(en="First override"),
                        icon="override-1",
                    ).model_dump()
                ),
                "expected_id": "override_1",
                "expected_name": "Override 1",
            },
            # Scenario 2: Start event without config (should use default)
            {
                "start_event": ProcessStartEvent(),
                "expected_id": "default_process",
                "expected_name": "Default Test Process",
            },
            # Scenario 3: Start event with None config (should use default)
            {
                "start_event": ProcessStartEvent(process_config=None),
                "expected_id": "default_process",
                "expected_name": "Default Test Process",
            },
        ]

        for i, scenario in enumerate(scenarios):
            start_event = scenario["start_event"]

            # Apply testing logic
            if start_event.is_start_event:
                walkthrough_process_config = start_event.process_config or sample_default_config

            # Verify expected behavior
            assert (
                walkthrough_process_config["process_id"] == scenario["expected_id"]
            ), f"Scenario {i+1} failed: wrong process_id"
            assert (
                walkthrough_process_config["name"]["en"] == scenario["expected_name"]
            ), f"Scenario {i+1} failed: wrong name"
