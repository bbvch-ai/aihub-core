from typing import Annotated, Any
from unittest.mock import AsyncMock, Mock, patch

import nats
import pytest
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import ProcessExceptionEvent, WorkEvent
from aihub_lib.nats.topic_managers.process.ProcessClassTopicManager import ProcessClassTopicManager
from aihub_lib.nats.topics.process.ProcessInstanceTopic import ProcessInstanceTopic
from aihub_lib.processes.ProcessConfig import ProcessConfig
from bson import ObjectId
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_process.agentic_processes.AgenticProcess import AgenticProcess
from aihub_process.context.walkthrough.WalkthroughContext import WalkthroughContext
from aihub_process.delegators.process.Process import Process
from aihub_process.dispatchers.ProcessDispatcher import ProcessDispatcher
from aihub_process.i18n.ProcessLocaleHandler import ProcessLocaleHandler
from aihub_process.process.decorators.process_step import process_step
from playground.events.CustomProcessStopEvent import CustomProcessStopEvent
from playground.events.InitialProcessWorkEvent import InitialProcessWorkEvent

enable_logging()


class MockProcess(AgenticProcess):
    """Mock process for testing purposes."""

    @process_step()
    async def start_step(
        self,
        work_from_initial_process: Annotated[
            InitialProcessWorkEvent, Process.In(process_class="InitialProcess", process_id="initial_process")
        ],
    ) -> Annotated[CustomProcessStopEvent, Process.Out()]:
        payload_from_initial = work_from_initial_process.process_stop_event.payload
        print(f"[SubsequentProcess.step] From InitialProcess: {payload_from_initial}")

        final_payload = f"{payload_from_initial} -> SubsequentProcess output"
        return CustomProcessStopEvent(payload=final_payload)


@pytest.fixture
def mock_process_config():
    """Create a mock process configuration."""
    return ProcessConfig(
        process_class="MockProcess",
        process_id="test_process",
        name=LocaleString(en="Test Process"),
        description=LocaleString(en="Test process for dispatcher testing"),
        icon="test-icon",
    )


@pytest.fixture
def mock_initial_process_stop_event():
    """Create a mock InitialProcessWorkEvent for testing."""
    return CustomProcessStopEvent(payload="InitialProcess output")


@pytest.fixture
def redis_client():
    """Create a stateful mocked Redis client for testing."""
    # Create a dictionary to simulate Redis storage
    redis_data = {}

    mock_redis = AsyncMock(spec=Redis)

    # Create stateful mock methods that actually store/retrieve data
    async def mock_get(key):
        return redis_data.get(key)

    async def mock_set(key, value, ex=None, px=None, nx=False, xx=False):
        if nx and key in redis_data:
            return False
        if xx and key not in redis_data:
            return False
        # Store as bytes to match real Redis behavior
        redis_data[key] = value.encode() if isinstance(value, str) else value
        return True

    async def mock_delete(key):
        return redis_data.pop(key, None) is not None

    async def mock_hget(name, key):
        hash_data = redis_data.get(name, {})
        if isinstance(hash_data, dict):
            return hash_data.get(key)
        return None

    async def mock_hset(name, key, value):
        if name not in redis_data:
            redis_data[name] = {}
        if isinstance(redis_data[name], dict):
            redis_data[name][key] = value
        return 1

    async def mock_hdel(name, key):
        hash_data = redis_data.get(name, {})
        if isinstance(hash_data, dict) and key in hash_data:
            del hash_data[key]
            return 1
        return 0

    async def mock_exists(key):
        return key in redis_data

    async def mock_keys(pattern="*"):
        return list(redis_data.keys())

    async def mock_flushdb():
        redis_data.clear()
        return True

    # Assign the mock methods
    mock_redis.get = mock_get
    mock_redis.set = mock_set
    mock_redis.delete = mock_delete
    mock_redis.hget = mock_hget
    mock_redis.hset = mock_hset
    mock_redis.hdel = mock_hdel
    mock_redis.exists = mock_exists
    mock_redis.keys = mock_keys
    mock_redis.flushdb = mock_flushdb

    return mock_redis


@pytest.fixture
def nats_client():
    """Create a NATS client for testing."""
    # For integration testing, use a minimal mock that behaves like NATS
    mock_nc = Mock(spec=nats.NATS)
    mock_nc.is_connected = True
    mock_nc.publish = AsyncMock()
    mock_nc.subscribe = AsyncMock()
    mock_nc.request = AsyncMock()
    return mock_nc


@pytest.fixture
def jetstream_context():
    """Create a JetStream context for testing."""
    mock_js = Mock(spec=JetStreamContext)
    mock_js.publish = AsyncMock()
    mock_js.subscribe = AsyncMock()
    mock_js.add_stream = AsyncMock()
    return mock_js


@pytest.fixture
def topic_manager():
    """Create a topic manager for testing."""
    mock_manager = Mock(spec=ProcessClassTopicManager)
    mock_manager.process_class = "MockProcess"
    mock_manager.get_process_class_topic = Mock(return_value="process.MockProcess")
    mock_manager.get_process_thread_topic_manager = Mock()
    # Mock the get_stream method that BaseDispatcher needs
    mock_manager.get_stream = Mock(return_value=("test_stream", "process.MockProcess.*"))
    return mock_manager


@pytest.fixture
def locale_handler():
    """Create a locale handler for testing."""
    handler = Mock(spec=ProcessLocaleHandler)
    handler.extract_multi_locale.return_value = "Test Process"
    handler.in_locale.return_value = handler
    return handler


@pytest.fixture
def process_topic():
    """Create a test process topic."""
    return ProcessInstanceTopic(
        process_class="MockProcess",
        process_id="test_process",
        process_walkthrough_id=str(ObjectId()),
        event_id=str(ObjectId()),
        event_type="work_event",
        event_name="InitialProcessWorkEvent",
    )


@pytest.fixture
def process_dispatcher(
    mock_process_config, nats_client, jetstream_context, redis_client, topic_manager, locale_handler
):
    """Create a real ProcessDispatcher instance for testing with minimal mocking."""
    # Create the dispatcher with real instantiation
    dispatcher = ProcessDispatcher(
        process=MockProcess,
        process_config=mock_process_config,
        nc=nats_client,
        js=jetstream_context,
        redis=redis_client,
        topic_manager=topic_manager,
        locale_handler=locale_handler,
    )

    # Only mock the methods that would interact with external services during testing
    # Mock the stores since they would require actual database connections
    dispatcher.event_store = Mock()
    dispatcher.event_store.get_events_of_multiple_types = AsyncMock(return_value={})
    dispatcher.event_store.delete_all = AsyncMock()
    dispatcher.step_store = Mock()
    dispatcher.step_store.mark_execution_context_as_crashed = AsyncMock()
    dispatcher.step_store.delete_all = AsyncMock()
    dispatcher.step_store.get_execution_count = AsyncMock(return_value=0)
    dispatcher.step_store.was_called_with_events = AsyncMock(return_value=False)
    dispatcher.step_store.report_execution_context_with_events = AsyncMock()
    dispatcher._step_meets_basic_execution_requirements = AsyncMock(return_value=True)

    # Mock publisher methods to avoid actual NATS publishing during tests
    dispatcher.js_publisher = Mock()
    dispatcher.nc_publisher = Mock()

    return dispatcher


class TestProcessDispatcherHandleEvent:
    """Test cases for ProcessDispatcher.handle_event method."""

    @pytest.mark.asyncio
    async def test_handle_start_event_with_process_config(
        self,
        process_dispatcher,
        process_topic,
        mock_process_config,
        mock_initial_process_stop_event,
    ):
        """Test handling InitialProcessWorkEvent with process config sets up context correctly."""
        # Arrange
        custom_config = ProcessConfig(
            process_class="MockProcess",
            process_id="custom_process",
            name=LocaleString(en="Custom Process"),
            description=LocaleString(en="Custom test process"),
            icon="custom-icon",
        )

        start_event = InitialProcessWorkEvent(
            process_config=custom_config.model_dump(), process_stop_event=mock_initial_process_stop_event
        )

        # Mock only the external dependencies and tracing
        with (
            patch.object(process_dispatcher, "is_step_ready", return_value=False),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await process_dispatcher.handle_event(start_event, process_topic)

            # Assert - Check that the config was properly stored in the real context
            walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)
            stored_config = await walkthrough_context.get("_process_config")
            assert stored_config == custom_config.model_dump()

    @pytest.mark.asyncio
    async def test_handle_start_event_without_process_config_uses_default(
        self,
        process_dispatcher,
        process_topic,
        mock_process_config,
        mock_initial_process_stop_event,
    ):
        """Test handling InitialProcessWorkEvent without process config uses default config."""
        # Arrange
        start_event = InitialProcessWorkEvent(process_stop_event=mock_initial_process_stop_event)

        with (
            patch.object(process_dispatcher, "is_step_ready", return_value=False),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await process_dispatcher.handle_event(start_event, process_topic)

            # Assert - Check that default config was used
            walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)
            stored_config = await walkthrough_context.get("_process_config")
            # Compare without private fields like _form_name
            assert stored_config == mock_process_config.model_dump(exclude={"_form_name"})

    @pytest.mark.asyncio
    async def test_handle_stop_event_cleans_up_context(self, process_dispatcher, process_topic):
        """Test handling StopEvent cleans up walkthrough context and stores."""
        # Arrange - First set up some data in the context
        stop_event = CustomProcessStopEvent(payload="Test stop event")
        walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)
        await walkthrough_context.set("_process_config", process_dispatcher.process_config.model_dump())
        await walkthrough_context.set("test_data", "test_value")

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await process_dispatcher.handle_event(stop_event, process_topic)

            # Assert - Check that context was actually cleaned up and stores called
            # Note: The actual context deletion behavior depends on the real WalkthroughContext implementation
            # We can verify the stores were called for cleanup
            process_dispatcher.event_store.delete_all.assert_called_once_with(process_topic.execution_context_id)
            process_dispatcher.step_store.delete_all.assert_called_once_with(process_topic.execution_context_id)

    @pytest.mark.asyncio
    async def test_handle_exception_event_marks_execution_context_crashed(self, process_dispatcher, process_topic):
        """Test handling ProcessExceptionEvent marks execution context as crashed."""
        # Arrange
        exception_event = ProcessExceptionEvent(message="Test exception")

        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.get = AsyncMock(return_value=process_dispatcher.process_config.model_dump())

        with (
            patch(
                "aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext", return_value=mock_walkthrough_context
            ),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await process_dispatcher.handle_event(exception_event, process_topic)

                # Assert
                process_dispatcher.step_store.mark_execution_context_as_crashed.assert_called_once_with(
                    process_topic.execution_context_id
                )

    @pytest.mark.asyncio
    async def test_handle_event_triggers_ready_steps(
        self, process_dispatcher, process_topic, mock_initial_process_stop_event
    ):
        """Test that handle_event triggers steps that are ready to execute."""
        # Arrange
        start_event = InitialProcessWorkEvent(process_stop_event=mock_initial_process_stop_event)

        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.set = AsyncMock()
        mock_walkthrough_context.get = AsyncMock(return_value=process_dispatcher.process_config.model_dump())

        # Use the actual MockProcess step method
        mock_step_method = MockProcess.start_step
        process_dispatcher.process.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock step readiness is already set up in the fixture

        with (
            patch(
                "aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext", return_value=mock_walkthrough_context
            ),
            patch.object(process_dispatcher, "is_step_ready", return_value=True) as mock_is_ready,
            patch.object(process_dispatcher, "execute_step"),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Mock asyncio task creation
                mock_task = Mock()
                mock_task.add_done_callback = Mock()

                with patch("asyncio.create_task", return_value=mock_task):
                    # Act
                    await process_dispatcher.handle_event(start_event, process_topic)

                    # Assert
                    mock_is_ready.assert_called_once()
                    assert len(process_dispatcher._background_tasks) == 1

    @pytest.mark.asyncio
    async def test_handle_event_retrieves_process_config_from_context_for_non_start_events(
        self, process_dispatcher, process_topic
    ):
        """Test that non-start events retrieve process config from walkthrough context."""
        # Arrange - First store config in context
        stored_config = process_dispatcher.process_config.model_dump()

        # Pre-populate the context with config
        walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)
        await walkthrough_context.set("_process_config", stored_config)

        # Now test with a control event
        work_event = WorkEvent()
        process_dispatcher.process.get_steps_waiting_for_event = Mock(return_value=[])

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await process_dispatcher.handle_event(work_event, process_topic)

            # Assert - Verify that the config was successfully retrieved from the real context
            # The fact that the method completes without error indicates successful config retrieval
            # We can verify by checking the context directly
            retrieved_config = await walkthrough_context.get("_process_config")
            assert retrieved_config == stored_config

    @pytest.mark.asyncio
    async def test_handle_event_raises_error_when_no_process_config_found(self, process_dispatcher, process_topic):
        """Test that handle_event raises ValueError when no process config is found."""
        # Arrange - Use a control event without any pre-stored config
        work_event = WorkEvent()

        # Ensure the context is empty (no config stored)
        walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)
        await walkthrough_context.delete("_process_config")  # Make sure no config exists

        with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            # Act & Assert - The real context should return None, causing the ValueError
            with pytest.raises(ValueError, match="No process config found"):
                await process_dispatcher.handle_event(work_event, process_topic)


class TestProcessDispatcherErrorHandling:
    """Test cases for error handling in ProcessDispatcher."""

    @pytest.mark.asyncio
    async def test_handle_event_with_invalid_process_config_type(
        self,
        process_dispatcher,
        process_topic,
        mock_initial_process_stop_event,
    ):
        """Test handling of invalid process config type validation."""
        # Arrange
        # Create a config missing required fields that aren't in non-configurable values
        invalid_config: dict[str, Any] = {"name": "invalid"}  # Missing required fields like process_class, process_id
        start_event = InitialProcessWorkEvent(
            process_config=invalid_config, process_stop_event=mock_initial_process_stop_event
        )

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act & Assert
            with pytest.raises(Exception):  # This would be a pydantic validation error
                await process_dispatcher.handle_event(start_event, process_topic)

    @pytest.mark.asyncio
    async def test_handle_event_with_context_setup_failure(
        self,
        process_dispatcher,
        process_topic,
        mock_initial_process_stop_event,
    ):
        """Test handling of context setup failures."""
        # Arrange
        start_event = InitialProcessWorkEvent(process_stop_event=mock_initial_process_stop_event)

        # Mock WalkthroughContext to raise an exception during initialization
        mock_walkthrough_context = Mock(spec=WalkthroughContext)
        mock_walkthrough_context.set = AsyncMock(side_effect=RuntimeError("Context setup failed"))

        with (
            patch(
                "aihub_process.dispatchers.ProcessDispatcher.WalkthroughContext", return_value=mock_walkthrough_context
            ),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act & Assert
            with pytest.raises(RuntimeError, match="Context setup failed"):
                await process_dispatcher.handle_event(start_event, process_topic)


class TestProcessDispatcherIntegration:
    """Integration test cases for ProcessDispatcher."""

    @pytest.mark.asyncio
    async def test_full_event_processing_flow(self, process_dispatcher, process_topic, mock_initial_process_stop_event):
        """Test the complete flow from event receipt to step execution with minimal mocking."""
        # Arrange
        custom_config = ProcessConfig(
            process_class="MockProcess",
            process_id="integration_test_process",
            name=LocaleString(en="Integration Test Process"),
            description=LocaleString(en="Process for testing complete flow"),
            icon="integration-icon",
        )

        start_event = InitialProcessWorkEvent(
            process_config=custom_config.model_dump(), process_stop_event=mock_initial_process_stop_event
        )

        # Use the actual MockProcess start_step method
        mock_step_method = MockProcess.start_step
        process_dispatcher.process.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock only the truly external dependencies
        from aihub_lib.nats.dispatcher.BaseDispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        process_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        with (
            patch.object(process_dispatcher, "is_step_ready", return_value=True),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
            patch("asyncio.create_task") as mock_create_task,
        ):
            mock_base_handle.return_value = None

            mock_task = Mock()
            mock_task.add_done_callback = Mock()
            mock_create_task.return_value = mock_task

            # Act
            await process_dispatcher.handle_event(start_event, process_topic)

            # Assert - verify complete flow using real context verification
            walkthrough_context = WalkthroughContext(process_dispatcher.redis, process_topic.process_walkthrough_id)

            # 1. Config should be stored in real context
            stored_config = await walkthrough_context.get("_process_config")
            assert stored_config == custom_config.model_dump()

            # 2. Step should be checked for readiness
            process_dispatcher.is_step_ready.assert_called_once()

            # 3. Background task should be created for step execution
            assert len(process_dispatcher._background_tasks) == 1
            mock_task.add_done_callback.assert_called_once()
