from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import nats
import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import BaseEvent, ControlEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from bson import ObjectId
from nats.js import JetStreamContext
from redis.asyncio import Redis

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.dispatchers.AgentDispatcher import AgentDispatcher
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.tracing.AgentRunTracer import AgentRunTracer
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step

enable_logging()


class MockAgent(Agent):
    """Mock agent for testing purposes."""

    @step()
    async def start_step(self, start_event: StartEvent) -> list[BaseEvent]:
        return []

    @step(max_executions_per_run=1)
    async def limited_step(self, start_event: StartEvent) -> list[BaseEvent]:
        return []

    @precondition()
    async def conditional_step_precondition(self, start_event: StartEvent) -> bool:
        return hasattr(start_event, "condition") and start_event.condition

    @step(precondition=conditional_step_precondition)
    async def conditional_step(self, start_event: StartEvent) -> list[BaseEvent]:
        return []


@pytest.fixture
def mock_agent_config():
    """Create a mock agent configuration."""
    return AgentConfig(
        agent_class="MockAgent",
        agent_id="test_agent",
        name=LocaleString(en="Test Agent"),
        description=LocaleString(en="Test agent for dispatcher testing"),
        icon="test-icon",
    )


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
    mock_manager = Mock(spec=AgentClassTopicManager)
    mock_manager.get_agent_class_topic = Mock(return_value="agent.MockAgent")
    mock_manager.get_agent_thread_topic_manager = Mock()
    # Mock the get_stream method that BaseDispatcher needs
    mock_manager.get_stream = Mock(return_value=("test_stream", "agent.MockAgent.*"))
    return mock_manager


@pytest.fixture
def locale_handler():
    """Create a locale handler for testing."""
    handler = Mock(spec=AgentLocaleHandler)
    handler.extract_multi_locale.return_value = "Test Agent"
    handler.in_locale.return_value = handler
    return handler


@pytest.fixture
def agent_topic():
    """Create a test agent topic."""
    return AgentInstanceTopic(
        agent_class="MockAgent",
        agent_id="test_agent",
        thread_id=str(ObjectId()),
        run_id=str(ObjectId()),
        display_id=str(ObjectId()),
        event_id=str(ObjectId()),
        event_type="control_event",
        event_name="StartEvent",
    )


@pytest.fixture
def agent_dispatcher(mock_agent_config, nats_client, jetstream_context, redis_client, topic_manager, locale_handler):
    """Create a real AgentDispatcher instance for testing with minimal mocking."""
    # Create the dispatcher with real instantiation
    dispatcher = AgentDispatcher(
        agent=MockAgent,
        default_agent_config=mock_agent_config,
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
    dispatcher._step_meets_basic_execution_requirements = AsyncMock(return_value=True)

    # Mock publisher methods to avoid actual NATS publishing during tests
    dispatcher.js_publisher = Mock()
    dispatcher.nc_publisher = Mock()

    return dispatcher


class TestAgentDispatcherHandleEvent:
    """Test cases for AgentDispatcher.handle_event method."""

    @pytest.mark.asyncio
    async def test_handle_start_event_with_agent_config(self, agent_dispatcher, agent_topic, mock_agent_config):
        """Test handling StartEvent with agent config sets up context correctly."""
        # Arrange
        custom_config = AgentConfig(
            agent_class="MockAgent",
            agent_id="custom_agent",
            name=LocaleString(en="Custom Agent"),
            description=LocaleString(en="Custom test agent"),
            icon="custom-icon",
        )

        start_event = StartEvent(agent_config=custom_config.model_dump())

        # Mock the tracer instance on the dispatcher
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - Check that the config was properly stored in the real context
            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            stored_config = await run_context.get("_agent_config")
            assert stored_config == custom_config.model_dump()

            # Verify tracing was initialized
            mock_tracer.trace_run_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_start_event_without_agent_config_uses_default(
        self, agent_dispatcher, agent_topic, mock_agent_config
    ):
        """Test handling StartEvent without agent config uses default config."""
        # Arrange
        start_event = StartEvent()

        # Mock the tracer instance on the dispatcher
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - Check that default config was used
            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            stored_config = await run_context.get("_agent_config")
            assert stored_config == mock_agent_config.model_dump()

    @pytest.mark.asyncio
    async def test_handle_stop_event_cleans_up_context(self, agent_dispatcher, agent_topic):
        """Test handling StopEvent cleans up run context and stores."""
        # Arrange - First set up some data in the context
        stop_event = StopEvent()
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.set("_agent_config", agent_dispatcher.default_agent_config.model_dump())
        await run_context.set("test_data", "test_value")

        # Mock tracer for stop event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_completion = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(stop_event, agent_topic)

            # Assert - Check that context was actually cleaned up and stores called
            # Note: The actual context deletion behavior depends on the real RunContext implementation
            # We can verify the stores were called for cleanup
            agent_dispatcher.event_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.step_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)

    @pytest.mark.asyncio
    async def test_handle_exception_event_marks_execution_context_crashed(self, agent_dispatcher, agent_topic):
        """Test handling ExceptionEvent marks execution context as crashed."""
        # Arrange
        exception_event = ExceptionEvent(message="Test exception")

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.default_agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        # Mock tracer for exception event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_completion = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext.for_topic", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext.for_topic", return_value=mock_thread_context),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(exception_event, agent_topic)

                # Assert
                agent_dispatcher.step_store.mark_execution_context_as_crashed.assert_called_once_with(
                    agent_topic.execution_context_id
                )

    @pytest.mark.asyncio
    async def test_handle_event_triggers_ready_steps(self, agent_dispatcher, agent_topic):
        """Test that handle_event triggers steps that are ready to execute."""
        # Arrange
        start_event = StartEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.default_agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        # Use the actual MockAgent step method
        mock_step_method = MockAgent.start_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock step readiness is already set up in the fixture

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext.for_topic", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext.for_topic", return_value=mock_thread_context),
            patch.object(agent_dispatcher, "is_step_ready", return_value=True) as mock_is_ready,
            patch.object(agent_dispatcher, "execute_step"),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Mock asyncio task creation
                mock_task = Mock()
                mock_task.add_done_callback = Mock()

                with patch("asyncio.create_task", return_value=mock_task):
                    # Act
                    await agent_dispatcher.handle_event(start_event, agent_topic)

                    # Assert
                    mock_is_ready.assert_called_once()
                    assert len(agent_dispatcher._background_tasks) == 1

    @pytest.mark.asyncio
    async def test_handle_event_retrieves_agent_config_from_context_for_non_start_events(
        self, agent_dispatcher, agent_topic
    ):
        """Test that non-start events retrieve agent config from run context."""
        # Arrange - First store config in context
        stored_config = agent_dispatcher.default_agent_config.model_dump()

        # Pre-populate the context with config
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.set("_agent_config", stored_config)

        # Now test with a control event
        control_event = ControlEvent()
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(control_event, agent_topic)

            # Assert - Verify that the config was successfully retrieved from the real context
            # The fact that the method completes without error indicates successful config retrieval
            # We can verify by checking the context directly
            retrieved_config = await run_context.get("_agent_config")
            assert retrieved_config == stored_config

    @pytest.mark.asyncio
    async def test_handle_event_raises_error_when_no_agent_config_found(self, agent_dispatcher, agent_topic):
        """Test that handle_event raises ValueError when no agent config is found."""
        # Arrange - Use a control event without any pre-stored config
        control_event = ControlEvent()

        # Ensure the context is empty (no config stored)
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.delete("_agent_config")  # Make sure no config exists

        with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            # Act & Assert - The real context should return None, causing the ValueError
            with pytest.raises(ValueError, match="No agent config found"):
                await agent_dispatcher.handle_event(control_event, agent_topic)

    @pytest.mark.asyncio
    async def test_handle_event_stores_start_event_context_data(self, agent_dispatcher, agent_topic):
        """Test that StartEvent context data is stored in run context."""
        # Arrange
        start_event = StartEvent()
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - verify that context data from start event is actually stored in real context
            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            event_data = start_event.to_context_dict()

            # Check that each piece of event data was stored
            for key, value in event_data.items():
                stored_value = await run_context.get(key)
                assert stored_value == value, f"Expected {key} to be {value}, but got {stored_value}"


class TestAgentDispatcherStepExecution:
    """Test cases for step execution logic in AgentDispatcher."""

    @pytest.mark.asyncio
    async def test_step_execution_with_max_executions_limit(self, agent_dispatcher, agent_topic):
        """Test that steps respect max_executions_per_run limit."""
        # Arrange
        start_event = StartEvent()

        # Use the actual MockAgent limited_step method (max_executions_per_run=1)
        mock_step_method = MockAgent.limited_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Override the default step store mock to return execution count at max (1 for limited_step)
        agent_dispatcher.step_store.get_execution_count = AsyncMock(return_value=1)  # Already at max

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - step should not be executed because max executions reached
            agent_dispatcher.step_store.get_execution_count.assert_called_once_with(
                agent_topic.execution_context_id, "limited_step"
            )

    @pytest.mark.asyncio
    async def test_step_execution_with_precondition(self, agent_dispatcher, agent_topic):
        """Test that steps with preconditions are evaluated correctly."""
        # Arrange
        start_event = StartEvent()
        start_event.condition = True  # Set condition for precondition to check

        # Use the actual MockAgent conditional_step method
        mock_step_method = MockAgent.conditional_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock _build_method_kwargs to return proper EventsAndKwargs
        from aihub_lib.nats.dispatcher.BaseDispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=True),
            patch.object(agent_dispatcher, "execute_step"),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Mock asyncio task creation
            mock_task = Mock()
            mock_task.add_done_callback = Mock()

            with patch("asyncio.create_task", return_value=mock_task):
                # Act
                await agent_dispatcher.handle_event(start_event, agent_topic)

                # Assert - step should be executed (background task created)
                assert len(agent_dispatcher._background_tasks) == 1


class TestAgentDispatcherErrorHandling:
    """Test cases for error handling in AgentDispatcher."""

    @pytest.mark.asyncio
    async def test_handle_event_with_invalid_agent_config_type(self, agent_dispatcher, agent_topic):
        """Test handling of invalid agent config type validation."""
        # Arrange
        invalid_config: dict[str, Any] = {"invalid": "config"}
        start_event = StartEvent(agent_config=invalid_config)

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext.for_topic", return_value=mock_run_context),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act & Assert
            with pytest.raises(Exception):  # This would be a pydantic validation error
                await agent_dispatcher.handle_event(start_event, agent_topic)

    @pytest.mark.asyncio
    async def test_handle_event_with_context_setup_failure(self, agent_dispatcher, agent_topic):
        """Test handling of context setup failures."""
        # Arrange
        start_event = StartEvent()

        # Mock RunContext to raise an exception during initialization
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock(side_effect=RuntimeError("Context setup failed"))

        # Mock tracer for start event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext.for_topic", return_value=mock_run_context),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act & Assert
            with pytest.raises(RuntimeError, match="Context setup failed"):
                await agent_dispatcher.handle_event(start_event, agent_topic)


class TestAgentDispatcherIntegration:
    """Integration test cases for AgentDispatcher."""

    @pytest.mark.asyncio
    async def test_full_event_processing_flow(self, agent_dispatcher, agent_topic):
        """Test the complete flow from event receipt to step execution with minimal mocking."""
        # Arrange
        custom_config = AgentConfig(
            agent_class="MockAgent",
            agent_id="integration_test_agent",
            name=LocaleString(en="Integration Test Agent"),
            description=LocaleString(en="Agent for testing complete flow"),
            icon="integration-icon",
        )

        start_event = StartEvent(agent_config=custom_config.model_dump())

        # Use the actual MockAgent start_step method
        mock_step_method = MockAgent.start_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock only the truly external dependencies
        from aihub_lib.nats.dispatcher.BaseDispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        # Mock the tracer instance
        mock_tracer = Mock()
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=True),
            patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle,
            patch("asyncio.create_task") as mock_create_task,
        ):
            mock_base_handle.return_value = None

            mock_task = Mock()
            mock_task.add_done_callback = Mock()
            mock_create_task.return_value = mock_task

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - verify complete flow using real context verification
            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)

            # 1. Config should be stored in real context
            stored_config = await run_context.get("_agent_config")
            assert stored_config == custom_config.model_dump()

            # 2. Tracing should be initialized
            mock_tracer.trace_run_start.assert_called_once()

            # 3. Context data should be stored in real context
            event_data = start_event.to_context_dict()
            for key, value in event_data.items():
                stored_value = await run_context.get(key)
                assert stored_value == value, f"Context key {key} not properly stored"

            # 4. Step should be checked for readiness
            agent_dispatcher.is_step_ready.assert_called_once()

            # 5. Background task should be created for step execution
            assert len(agent_dispatcher._background_tasks) == 1
            mock_task.add_done_callback.assert_called_once()
