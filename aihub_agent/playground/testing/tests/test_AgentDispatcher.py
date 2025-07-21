from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import BaseEvent, ControlEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.testing.logging.logger import enable_logging
from bson import ObjectId

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.dispatchers.AgentDispatcher import AgentDispatcher
from aihub_agent.i18n.AgentLocaleHandler import AgentLocaleHandler
from aihub_agent.tracing.coordinators.RunTraceCoordinator import RunTraceCoordinator
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
def mock_nc():
    """Mock NATS connection."""
    return Mock()


@pytest.fixture
def mock_js():
    """Mock JetStream context."""
    return Mock()


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    return Mock()


@pytest.fixture
def mock_topic_manager():
    """Mock topic manager."""
    return Mock()


@pytest.fixture
def mock_locale_handler():
    """Mock locale handler."""
    handler = Mock(spec=AgentLocaleHandler)
    handler.extract_multi_locale.return_value = "Test Agent"
    handler.in_locale.return_value = handler
    return handler


@pytest.fixture
def agent_topic():
    """Create a test agent topic."""
    return AgentTopic(
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
def agent_dispatcher(mock_agent_config, mock_nc, mock_js, mock_redis, mock_topic_manager, mock_locale_handler):
    """Create an AgentDispatcher instance for testing."""
    with patch.multiple(
        "aihub_agent.dispatchers.AgentDispatcher.AgentDispatcher", __init__=lambda self, *args, **kwargs: None
    ):
        dispatcher = AgentDispatcher.__new__(AgentDispatcher)
        dispatcher.agent = MockAgent
        dispatcher.default_agent_config = mock_agent_config
        dispatcher.locale_handler = mock_locale_handler
        dispatcher.agent_config_type = type(mock_agent_config)
        dispatcher.nc = mock_nc
        dispatcher.js = mock_js
        dispatcher.redis = mock_redis
        dispatcher.topic_manager = mock_topic_manager
        dispatcher._background_tasks = set()

        # Mock inherited methods and attributes
        dispatcher.event_store = Mock()
        dispatcher.event_store.get_events_of_multiple_types = AsyncMock(return_value={})
        dispatcher.event_store.delete_all = AsyncMock()
        dispatcher.step_store = Mock()
        dispatcher.step_store.mark_execution_context_as_crashed = AsyncMock()
        dispatcher.step_store.delete_all = AsyncMock()
        dispatcher.step_store.get_execution_count = AsyncMock(return_value=0)
        dispatcher._step_meets_basic_execution_requirements = AsyncMock(return_value=True)
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

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        mock_thread_context = Mock(spec=ThreadContext)

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator") as mock_tracer_class,
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
        ):
            mock_tracer = Mock(spec=RunTraceCoordinator)
            mock_tracer.trace_run_start.return_value = {"trace": "headers"}
            mock_tracer_class.return_value = mock_tracer

            # Mock the base dispatcher call
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(start_event, agent_topic)

                # Assert
                mock_run_context.set.assert_any_call("_agent_config", custom_config.model_dump())
                mock_tracer.trace_run_start.assert_called_once()
                mock_run_context.set.assert_any_call("telemetry_headers", {"trace": "headers"})

    @pytest.mark.asyncio
    async def test_handle_start_event_without_agent_config_uses_default(
        self, agent_dispatcher, agent_topic, mock_agent_config
    ):
        """Test handling StartEvent without agent config uses default config."""
        # Arrange
        start_event = StartEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        mock_thread_context = Mock(spec=ThreadContext)

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator") as mock_tracer_class,
            patch.object(agent_dispatcher, "is_step_ready", return_value=False),
        ):
            mock_tracer = Mock(spec=RunTraceCoordinator)
            mock_tracer.trace_run_start.return_value = {"trace": "headers"}
            mock_tracer_class.return_value = mock_tracer

            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(start_event, agent_topic)

                # Assert
                mock_run_context.set.assert_any_call("_agent_config", mock_agent_config.model_dump())

    @pytest.mark.asyncio
    async def test_handle_stop_event_cleans_up_context(self, agent_dispatcher, agent_topic):
        """Test handling StopEvent cleans up run context and stores."""
        # Arrange
        stop_event = StopEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.delete_all = AsyncMock()
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.default_agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator"),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(stop_event, agent_topic)

                # Assert
                mock_run_context.delete_all.assert_called_once()
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

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator"),
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

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator") as mock_tracer_class,
            patch.object(agent_dispatcher, "is_step_ready", return_value=True) as mock_is_ready,
            patch.object(agent_dispatcher, "execute_step"),
        ):
            mock_tracer = Mock(spec=RunTraceCoordinator)
            mock_tracer.trace_run_start.return_value = {"trace": "headers"}
            mock_tracer_class.return_value = mock_tracer

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
        # Arrange
        control_event = ControlEvent()
        stored_config = agent_dispatcher.default_agent_config.model_dump()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=stored_config)

        mock_thread_context = Mock(spec=ThreadContext)

        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator"),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(control_event, agent_topic)

                # Assert
                mock_run_context.get.assert_called_once_with("_agent_config")

    @pytest.mark.asyncio
    async def test_handle_event_raises_error_when_no_agent_config_found(self, agent_dispatcher, agent_topic):
        """Test that handle_event raises ValueError when no agent config is found."""
        # Arrange
        control_event = ControlEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=None)

        mock_thread_context = Mock(spec=ThreadContext)

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act & Assert
                with pytest.raises(ValueError, match="No agent config found"):
                    await agent_dispatcher.handle_event(control_event, agent_topic)

    @pytest.mark.asyncio
    async def test_handle_event_stores_start_event_context_data(self, agent_dispatcher, agent_topic):
        """Test that StartEvent context data is stored in run context."""
        # Arrange
        start_event = StartEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        mock_thread_context = Mock(spec=ThreadContext)

        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[])

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator") as mock_tracer_class,
        ):
            mock_tracer = Mock(spec=RunTraceCoordinator)
            mock_tracer.trace_run_start.return_value = {"trace": "headers"}
            mock_tracer_class.return_value = mock_tracer

            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Act
                await agent_dispatcher.handle_event(start_event, agent_topic)

                # Assert - verify that context data from start event is stored
                event_data = start_event.to_context_dict()
                for key, value in event_data.items():
                    mock_run_context.set.assert_any_call(key, value)


class TestAgentDispatcherStepExecution:
    """Test cases for step execution logic in AgentDispatcher."""

    @pytest.mark.asyncio
    async def test_step_execution_with_max_executions_limit(self, agent_dispatcher, agent_topic):
        """Test that steps respect max_executions_per_run limit."""
        # Arrange
        start_event = StartEvent()

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.default_agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        # Use the actual MockAgent limited_step method (max_executions_per_run=1)
        mock_step_method = MockAgent.limited_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Override the default step store mock to return execution count at max (1 for limited_step)
        agent_dispatcher.step_store.get_execution_count = AsyncMock(return_value=1)  # Already at max

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator"),
        ):
            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
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

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.get = AsyncMock(return_value=agent_dispatcher.default_agent_config.model_dump())

        mock_thread_context = Mock(spec=ThreadContext)

        # For this test, we need more control over precondition behavior, so use a mock
        mock_step_method = Mock()
        mock_step_method.__name__ = "conditional_step"
        setattr(mock_step_method, Agent.INPUT_EVENTS_ANNOTATION, {StartEvent})
        
        # Mock precondition function that returns True when event has condition=True
        mock_precondition = AsyncMock(return_value=True)
        setattr(mock_step_method, Agent.PRECONDITION_FUNCTION_ANNOTATION, mock_precondition)
        setattr(mock_step_method, Agent.MAX_EXECUTION_PER_RUN_ANNOTATION, None)  # Ensure this is None, not Mock
        
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock _build_method_kwargs to return proper EventsAndKwargs
        from aihub_lib.nats.dispatcher.BaseDispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator"),
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

                    # Assert - step should be executed (background task created)
                    assert len(agent_dispatcher._background_tasks) == 1


class TestAgentDispatcherErrorHandling:
    """Test cases for error handling in AgentDispatcher."""

    @pytest.mark.asyncio
    async def test_handle_event_with_invalid_agent_config_type(self, agent_dispatcher, agent_topic):
        """Test handling of invalid agent config type validation."""
        # Arrange
        start_event = StartEvent(agent_config={"invalid": "config"})

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
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

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
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
        """Test the complete flow from event receipt to step execution."""
        # Arrange
        custom_config = AgentConfig(
            agent_class="MockAgent",
            agent_id="integration_test_agent",
            name=LocaleString(en="Integration Test Agent"),
            description=LocaleString(en="Agent for testing complete flow"),
            icon="integration-icon",
        )

        start_event = StartEvent(agent_config=custom_config.model_dump())

        mock_run_context = Mock(spec=RunContext)
        mock_run_context.set = AsyncMock()
        mock_run_context.get = AsyncMock()

        mock_thread_context = Mock(spec=ThreadContext)

        # Use the actual MockAgent start_step method
        mock_step_method = MockAgent.start_step
        agent_dispatcher.agent.get_steps_waiting_for_event = Mock(return_value=[mock_step_method])

        # Mock _build_method_kwargs to return proper EventsAndKwargs
        from aihub_lib.nats.dispatcher.BaseDispatcher import EventsAndKwargs

        mock_events_and_kwargs = EventsAndKwargs(events=[start_event], kwargs={"start_event": start_event})
        agent_dispatcher._build_method_kwargs = AsyncMock(return_value=mock_events_and_kwargs)

        # Mock execute_step to verify it gets called
        agent_dispatcher.execute_step = AsyncMock()

        with (
            patch("aihub_agent.dispatchers.AgentDispatcher.RunContext", return_value=mock_run_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.ThreadContext", return_value=mock_thread_context),
            patch("aihub_agent.dispatchers.AgentDispatcher.RunTraceCoordinator") as mock_tracer_class,
            patch.object(agent_dispatcher, "is_step_ready", return_value=True),
        ):
            mock_tracer = Mock()
            mock_tracer.trace_run_start.return_value = {"integration": "headers"}
            mock_tracer_class.return_value = mock_tracer

            with patch("aihub_lib.nats.dispatcher.BaseDispatcher.BaseDispatcher.handle_event") as mock_base_handle:
                mock_base_handle.return_value = None

                # Mock asyncio task creation
                mock_task = Mock()
                mock_task.add_done_callback = Mock()

                with patch("asyncio.create_task", return_value=mock_task):
                    # Act
                    await agent_dispatcher.handle_event(start_event, agent_topic)

                    # Assert - verify complete flow
                    # 1. Config should be stored
                    mock_run_context.set.assert_any_call("_agent_config", custom_config.model_dump())

                    # 2. Tracing should be initialized
                    mock_tracer.trace_run_start.assert_called_once()
                    mock_run_context.set.assert_any_call("telemetry_headers", {"integration": "headers"})

                    # 3. Context data should be stored
                    event_data = start_event.to_context_dict()
                    for key, value in event_data.items():
                        mock_run_context.set.assert_any_call(key, value)

                    # 4. Step should be checked for readiness
                    agent_dispatcher.is_step_ready.assert_called_once()

                    # 5. Background task should be created for step execution
                    assert len(agent_dispatcher._background_tasks) == 1
                    mock_task.add_done_callback.assert_called_once()
