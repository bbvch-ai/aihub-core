from fnmatch import fnmatch
import inspect
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import nats
import pytest
from bson import ObjectId
from nats.js import JetStreamContext
from redis.asyncio import Redis
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.dispatcher import StepStore
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import ControlEvent, ExceptionEvent, StartEvent, StopEvent
from swiss_ai_hub.core.form.normalization import transform_formkit_arrays
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.topic_managers import AgentClassTopicManager
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
from swiss_ai_hub.agent.tracing.agent_run_tracer import AgentRunTracer
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

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

    async def mock_delete(*keys):
        return sum(1 for key in keys if redis_data.pop(key, None) is not None)

    def mock_scan_iter(match=None, count=None):
        async def _iter():
            for key in list(redis_data):
                if match is None or fnmatch(key, match):
                    yield key

        return _iter()

    async def mock_incrby(key, amount):
        value = int(redis_data.get(key, b"0")) + amount
        redis_data[key] = str(value).encode()
        return value

    async def mock_expire(key, ttl):
        return True

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
    # scan_iter/incrby/expire let a real StepStore run against this fake. StoreBase.delete_all
    # logs and swallows its own errors, so without scan_iter it deletes nothing silently and
    # any ordering assertion would pass vacuously.
    mock_redis.scan_iter = mock_scan_iter
    mock_redis.incrby = mock_incrby
    mock_redis.expire = mock_expire
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
        agent_config=mock_agent_config,
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
    dispatcher.step_store.mark_execution_context_as_completed = AsyncMock()
    dispatcher.step_store.is_execution_context_crashed = AsyncMock(return_value=False)
    dispatcher.step_store.is_execution_context_completed = AsyncMock(return_value=False)
    dispatcher.step_store.delete_all = AsyncMock()
    dispatcher.step_store.get_execution_count = AsyncMock(return_value=0)
    dispatcher.trace_store = Mock()
    dispatcher.trace_store.delete_all = AsyncMock()
    dispatcher._step_meets_basic_execution_requirements = AsyncMock(return_value=True)

    # Mock publisher methods to avoid actual NATS publishing during tests
    dispatcher.js_publisher = Mock()
    dispatcher.nc_publisher = Mock()

    # Mock the config client to return the mock agent config
    dispatcher._config_client = Mock()
    dispatcher._config_client.fetch_config = AsyncMock(return_value=mock_agent_config.model_dump())

    return dispatcher


class TestAgentDispatcherHandleEvent:
    """Test cases for AgentDispatcher.handle_event method."""

    @pytest.mark.asyncio
    async def test_handle_start_event_fetches_config_via_rpc(self, agent_dispatcher, mock_agent_config):
        """Test handling StartEvent fetches config via RPC and sets up context correctly."""
        # Arrange - Create a topic with specific agent_id that we want to test
        custom_topic = AgentInstanceTopic(
            agent_class="MockAgent",
            agent_id="custom_agent",
            thread_id=str(ObjectId()),
            run_id=str(ObjectId()),
            display_id=str(ObjectId()),
            event_id=str(ObjectId()),
            event_type="control_event",
            event_name="StartEvent",
        )

        custom_config = AgentConfig(
            agent_id="custom_agent",
            name=LocaleString(en="Custom Agent"),
            description=LocaleString(en="Custom test agent"),
            icon="custom-icon",
        )

        # StartEvent no longer has agent_id - it comes from the topic
        start_event = StartEvent()

        # Mock the config client to return the custom config
        agent_dispatcher._config_client.fetch_config = AsyncMock(return_value=custom_config.model_dump())

        # Mock the tracer instance on the dispatcher
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act - agent_id comes from the topic, not the event
            await agent_dispatcher.handle_event(start_event, custom_topic)

            # Assert - Verify config was fetched via RPC using agent_id from topic
            agent_dispatcher._config_client.fetch_config.assert_called_once_with(
                agent_class="MockAgent",
                agent_id="custom_agent",
            )

            # Assert - Check that the config was properly stored in the real context
            run_context = RunContext.for_topic(agent_dispatcher.redis, custom_topic)
            stored_config = await run_context.get("_agent_config")
            assert stored_config["agent_id"] == "custom_agent"

            # Verify tracing was initialized
            mock_tracer.trace_run_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_start_event_uses_agent_id_from_topic(self, agent_dispatcher, agent_topic, mock_agent_config):
        """Test handling StartEvent uses agent_id from the topic (not the event) to fetch config."""
        # Arrange - agent_id comes from the topic, not the event
        start_event = StartEvent()

        # Mock the tracer instance on the dispatcher
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(start_event, agent_topic)

            # Assert - Check that config was fetched using agent_id from topic
            agent_dispatcher._config_client.fetch_config.assert_called_once_with(
                agent_class="MockAgent",
                agent_id="test_agent",  # This comes from agent_topic fixture
            )

            # Assert - Check that default config was used (from the mock)
            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            stored_config = await run_context.get("_agent_config")
            assert stored_config == mock_agent_config.model_dump()

    @pytest.mark.asyncio
    async def test_handle_stop_event_cleans_up_context(self, agent_dispatcher, agent_topic):
        """Test handling StopEvent cleans up run context and stores."""
        # Arrange - First set up some data in the context
        stop_event = StopEvent()
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.set("_agent_config", agent_dispatcher.agent_config.model_dump())
        await run_context.set("test_data", "test_value")

        # Mock tracer for stop event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.clear_run = Mock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act
            await agent_dispatcher.handle_event(stop_event, agent_topic)

            # Assert - Check that context was actually cleaned up and stores called
            # Note: The actual context deletion behavior depends on the real RunContext implementation
            # We can verify the stores were called for cleanup
            agent_dispatcher.event_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.step_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.trace_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.step_store.mark_execution_context_as_completed.assert_called_once_with(
                agent_topic.execution_context_id
            )

    @pytest.mark.asyncio
    async def test_handle_stop_event_does_not_require_agent_config(self, agent_dispatcher, agent_topic):
        """A terminal event must tear the run down even when the config is already gone."""
        stop_event = StopEvent()
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.delete("_agent_config")

        with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(stop_event, agent_topic)

            agent_dispatcher.event_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.step_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)
            agent_dispatcher.trace_store.delete_all.assert_called_once_with(agent_topic.execution_context_id)

    @pytest.mark.asyncio
    async def test_redelivered_stop_event_skips_second_teardown(self, agent_dispatcher, agent_topic):
        """A redelivered StopEvent after teardown must neither error nor tear down again."""
        stop_event = StopEvent()
        agent_dispatcher.step_store.is_execution_context_completed = AsyncMock(return_value=True)

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.delete_all = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(stop_event, agent_topic)

            mock_run_context.delete_all.assert_not_called()
            agent_dispatcher.event_store.delete_all.assert_not_called()
            agent_dispatcher.step_store.delete_all.assert_not_called()
            agent_dispatcher.trace_store.delete_all.assert_not_called()
            agent_dispatcher.step_store.mark_execution_context_as_completed.assert_not_called()

    @pytest.mark.asyncio
    async def test_redelivered_exception_event_skips_second_teardown(self, agent_dispatcher, agent_topic):
        """A redelivered ExceptionEvent after a crash teardown must not tear down or re-mark."""
        exception_event = ExceptionEvent(message="Test exception")
        agent_dispatcher.step_store.is_execution_context_crashed = AsyncMock(return_value=True)

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.delete_all = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(exception_event, agent_topic)

            mock_run_context.delete_all.assert_not_called()
            agent_dispatcher.event_store.delete_all.assert_not_called()
            agent_dispatcher.step_store.mark_execution_context_as_crashed.assert_not_called()

    @pytest.mark.asyncio
    async def test_redelivered_event_after_teardown_returns_quietly(self, agent_dispatcher, agent_topic):
        """A redelivered mid-run event after teardown must not raise, dispatch steps, or touch run context."""
        control_event = ControlEvent()
        control_event._aihub_headers = {"X-AIHub-Token": "token"}
        agent_dispatcher.step_store.is_execution_context_completed = AsyncMock(return_value=True)
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=None)
        mock_run_context.set = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(control_event, agent_topic)

            mock_run_context.set.assert_not_called()
            agent_dispatcher.agent.get_steps_waiting_for_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_redelivered_start_event_after_teardown_skips_run(self, agent_dispatcher, agent_topic):
        """A redelivered StartEvent after teardown must not re-fetch config or replay the workflow."""
        start_event = StartEvent()
        agent_dispatcher.step_store.is_execution_context_completed = AsyncMock(return_value=True)
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(start_event, agent_topic)

            agent_dispatcher._config_client.fetch_config.assert_not_called()
            mock_run_context.set.assert_not_called()
            agent_dispatcher.agent.get_steps_waiting_for_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_redelivered_terminal_event_is_a_no_op_against_a_real_step_store(
        self, agent_dispatcher, agent_topic, redis_client
    ):
        """Teardown must leave a marker that outlives its own deletes.

        The other redelivery tests stub ``is_execution_context_completed`` to True, so they prove
        the skip branch works *given* a marker but never that teardown produces one. A real
        StepStore is used here so the marker is written and read through real Redis keys: teardown
        clears ``steps:{id}:*`` while markers live under ``step_markers:{id}:*``, and this asserts
        the marker is genuinely still readable afterwards rather than mocked into existence.
        """
        agent_dispatcher.step_store = StepStore(redis_client)
        stop_event = StopEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.delete_all = AsyncMock()
        mock_run_context.get = AsyncMock(return_value=None)
        mock_run_context.set = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(stop_event, agent_topic)

            assert await agent_dispatcher.step_store.is_execution_context_completed(agent_topic.execution_context_id), (
                "teardown left no completed marker — its own deletes wiped it"
            )

            await agent_dispatcher.handle_event(stop_event, agent_topic)

            assert agent_dispatcher.event_store.delete_all.call_count == 1, (
                "redelivered terminal event tore the run down a second time"
            )
            assert mock_run_context.delete_all.call_count == 1

    @pytest.mark.asyncio
    async def test_handle_exception_event_marks_execution_context_crashed(self, agent_dispatcher, agent_topic):
        """Test handling ExceptionEvent marks execution context as crashed."""
        # Arrange
        exception_event = ExceptionEvent(message="Test exception")

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        # Mock tracer for exception event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.clear_run = Mock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.ThreadContext.for_topic",
                return_value=mock_thread_context,
            ),
        ):
            with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
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
        # Arrange - agent_id comes from the topic, not the event
        start_event = StartEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.agent_config.model_dump())

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
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.ThreadContext.for_topic",
                return_value=mock_thread_context,
            ),
            patch.object(agent_dispatcher, "is_step_ready", return_value=True) as mock_is_ready,
            patch.object(agent_dispatcher, "execute_step"),
        ):
            with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
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
        stored_config = agent_dispatcher.agent_config.model_dump()

        # Pre-populate the context with config
        run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
        await run_context.set("_agent_config", stored_config)

        # Now test with a control event
        control_event = ControlEvent()
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        with (
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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

        with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            # Act & Assert - The real context should return None, causing the ValueError
            with pytest.raises(ValueError, match="No agent config found"):
                await agent_dispatcher.handle_event(control_event, agent_topic)

    @pytest.mark.asyncio
    async def test_handle_event_stores_start_event_context_data(self, agent_dispatcher, agent_topic):
        """Test that StartEvent context data is stored in run context."""
        # Arrange - agent_id comes from the topic, not the event
        start_event = StartEvent()
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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
        # Arrange - agent_id comes from the topic, not the event
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
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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
        # Arrange - agent_id comes from the topic, not the event
        start_event = StartEvent()
        start_event.condition = True  # Set condition for precondition to check

        # Use the actual MockAgent conditional_step method
        mock_step_method = MockAgent.conditional_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock _build_method_kwargs to return proper EventsAndKwargs
        from swiss_ai_hub.core.dispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        # Mock the tracer instance
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=True),
            patch.object(agent_dispatcher, "execute_step"),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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
    async def test_handle_event_with_invalid_agent_config_from_rpc(self, agent_dispatcher, agent_topic):
        """Test handling of invalid agent config returned by RPC."""
        # Arrange - agent_id comes from the topic, not the event
        invalid_config: dict[str, Any] = {"invalid": "config"}
        start_event = StartEvent()

        # Mock the config client to return invalid config
        agent_dispatcher._config_client.fetch_config = AsyncMock(return_value=invalid_config)

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
        ):
            mock_base_handle.return_value = None

            # Act & Assert
            with pytest.raises(Exception):  # This would be a pydantic validation error
                await agent_dispatcher.handle_event(start_event, agent_topic)

    @pytest.mark.asyncio
    async def test_handle_event_with_context_setup_failure(self, agent_dispatcher, agent_topic):
        """Test handling of context setup failures."""
        # Arrange - agent_id comes from the topic, not the event
        start_event = StartEvent()

        # Mock RunContext to raise an exception during initialization
        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock(side_effect=RuntimeError("Context setup failed"))

        # Mock tracer for start event processing
        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch(
                "swiss_ai_hub.agent.dispatchers.agent_dispatcher.RunContext.for_topic", return_value=mock_run_context
            ),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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
            agent_id="integration_test_agent",
            name=LocaleString(en="Integration Test Agent"),
            description=LocaleString(en="Agent for testing complete flow"),
            icon="integration-icon",
        )

        # agent_id comes from the topic, not the event
        start_event = StartEvent()

        # Mock the config client to return the custom config
        agent_dispatcher._config_client.fetch_config = AsyncMock(return_value=custom_config.model_dump())

        # Use the actual MockAgent start_step method
        mock_step_method = MockAgent.start_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock only the truly external dependencies
        from swiss_ai_hub.core.dispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        # Mock the tracer instance
        mock_tracer = Mock()
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with (
            patch.object(agent_dispatcher, "is_step_ready", return_value=True),
            patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle,
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
            assert stored_config["agent_id"] == "integration_test_agent"

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


class TestTransformFormkitArrays:
    """Tests for the transform_formkit_arrays function."""

    def test_transforms_dict_with_numeric_keys_and_dict_values_to_list(self):
        """Test that dict with numeric string keys and dict values is converted to a list."""
        data = {"0": {"name": "item1"}, "1": {"name": "item2"}}
        result = transform_formkit_arrays(data)
        assert result == [{"name": "item1"}, {"name": "item2"}]

    def test_preserves_dict_with_numeric_keys_and_primitive_values(self):
        """Test that dict with numeric string keys but primitive values is NOT converted."""
        # This is the new conservative behavior - primitive values means it's not a FormKit array
        data = {"0": "value1", "1": "value2"}
        result = transform_formkit_arrays(data)
        # Should NOT be converted because values are primitives, not dicts
        assert result == {"0": "value1", "1": "value2"}

    def test_preserves_regular_dict(self):
        """Test that regular dicts with non-numeric keys are preserved."""
        data = {"name": "test", "value": 123}
        result = transform_formkit_arrays(data)
        assert result == {"name": "test", "value": 123}

    def test_transforms_nested_formkit_arrays(self):
        """Test that nested FormKit arrays are properly transformed."""
        data = {
            "items": {
                "0": {"subItems": {"0": {"name": "nested1"}, "1": {"name": "nested2"}}},
                "1": {"subItems": {"0": {"name": "nested3"}}},
            }
        }
        result = transform_formkit_arrays(data)
        expected = {
            "items": [
                {"subItems": [{"name": "nested1"}, {"name": "nested2"}]},
                {"subItems": [{"name": "nested3"}]},
            ]
        }
        assert result == expected

    def test_preserves_lists(self):
        """Test that regular lists are preserved (items are recursively transformed)."""
        data = [{"0": {"a": 1}, "1": {"b": 2}}, {"name": "test"}]
        result = transform_formkit_arrays(data)
        expected = [[{"a": 1}, {"b": 2}], {"name": "test"}]
        assert result == expected

    def test_preserves_primitives(self):
        """Test that primitive values are returned as-is."""
        assert transform_formkit_arrays("string") == "string"
        assert transform_formkit_arrays(123) == 123
        assert transform_formkit_arrays(True) is True
        assert transform_formkit_arrays(None) is None


class TestAgentDispatcherAihubHeaders:
    """RunContext is the authorized place where steps can pick up X-AIHub-* identity headers."""

    @pytest.mark.asyncio
    async def test_handle_event_stores_aihub_headers_from_message_into_run_context(self, agent_dispatcher, agent_topic):
        # Keys are lowercased on the way in (see NATSMessageHeaders.extract_aihub_headers).
        start_event = StartEvent()
        start_event._aihub_headers = {"x-aihub-user-token": "tok-from-api"}
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(start_event, agent_topic)

            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            stored = await run_context.get(agent_dispatcher._AIHUB_HEADERS_KEY)
            assert stored == {"x-aihub-user-token": "tok-from-api"}

    @pytest.mark.asyncio
    async def test_handle_event_does_not_persist_aihub_headers_when_message_has_none(
        self, agent_dispatcher, agent_topic
    ):
        # No headers on the event — the key must remain unset.
        start_event = StartEvent()
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        mock_tracer = Mock(spec=AgentRunTracer)
        mock_tracer.trace_run_start = AsyncMock(return_value=None)
        agent_dispatcher.agent_run_tracer = mock_tracer

        with patch("swiss_ai_hub.core.dispatcher.base_dispatcher.BaseDispatcher.handle_event") as mock_base_handle:
            mock_base_handle.return_value = None

            await agent_dispatcher.handle_event(start_event, agent_topic)

            run_context = RunContext.for_topic(agent_dispatcher.redis, agent_topic)
            assert await run_context.get(agent_dispatcher._AIHUB_HEADERS_KEY) is None


class UserInjectionAgent(Agent):
    """Declares the two annotation shapes a step can use for the invoking user."""

    @step()
    async def required_user_step(self, start_event: StartEvent, user: UserIdentity) -> list[BaseEvent]:
        return []

    @step()
    async def optional_user_step(self, start_event: StartEvent, user: UserIdentity | None = None) -> list[BaseEvent]:
        return []


class TestUserIdentityInjection:
    """The programmatically-started agents annotate the user `UserIdentity | None`.

    An equality check against the bare class silently misses that union: the kwarg is dropped, the
    parameter keeps its `= None` default, and the run authenticates with the master key while looking
    correctly wired. Nothing else catches it — the type checker sees a valid optional parameter and
    every conversational agent uses the bare annotation, so the chat path stays green.
    """

    @staticmethod
    def _param(step_name: str) -> inspect.Parameter:
        return inspect.signature(getattr(UserInjectionAgent, step_name)).parameters["user"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("step_name", ["required_user_step", "optional_user_step"])
    async def test_injects_the_user_for_both_annotation_shapes(self, agent_dispatcher, agent_topic, step_name):
        user = UserIdentity(id="u1", name="Tester", email="t@example.com", is_sys_admin=False, roles=[])
        run_context = Mock()
        run_context.get = AsyncMock(return_value=user.model_dump(mode="json"))

        value = await agent_dispatcher._get_parameter_value(
            self._param(step_name), {}, Mock(), run_context, Mock(), agent_topic
        )

        assert isinstance(value, UserIdentity), f"{step_name} did not receive a UserIdentity"
        assert value.id == "u1"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("step_name", ["required_user_step", "optional_user_step"])
    async def test_yields_none_when_the_run_carries_no_user(self, agent_dispatcher, agent_topic, step_name):
        run_context = Mock()
        run_context.get = AsyncMock(return_value=None)

        value = await agent_dispatcher._get_parameter_value(
            self._param(step_name), {}, Mock(), run_context, Mock(), agent_topic
        )

        assert value is None
