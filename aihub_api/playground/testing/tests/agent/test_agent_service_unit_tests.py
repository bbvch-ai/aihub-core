from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import AgentClassDiscoveryResponseEvent
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from bson import ObjectId
from fastapi import HTTPException

from aihub_api.routes.agent.AgentService import (
    DISCOVER_AGENTS_CACHE,
    GET_AGENT_CLASS_CACHE,
    GET_AGENT_INSTANCE_CACHE,
    AgentService,
)
from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO
from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.thread.ThreadService import ThreadService

enable_logging()


@pytest.fixture(autouse=True)
def cleanup_db_and_cache(sample_agent_config):
    AgentService._clear_cache()
    yield
    AgentService._clear_cache()


@pytest.fixture
def sample_agent_config():
    """Create a sample AgentConfig for testing."""
    return AgentConfig(
        agent_class="TestAgent",
        agent_id="test_agent_1",
        name=LocaleString(en="Test Agent 1"),
        description=LocaleString(en="A test agent for validation"),
        icon="test-icon",
    )


@pytest.fixture
def sample_agent_class(sample_agent_config):
    """Create a sample AgentClass for testing."""
    mock_agent_class = Mock(spec=AgentClassDTO)
    mock_agent_class.agent_class = "TestAgent"
    mock_agent_class.default_agent_config = sample_agent_config
    mock_agent_class.agent_config_specs = []
    mock_agent_class.is_conversational = True
    mock_agent_class.start_events = []
    mock_agent_class.stop_events = []
    mock_agent_class.is_online = True
    return mock_agent_class


@pytest.fixture
def sample_agent_instance(sample_agent_class, sample_agent_config):
    """Create a sample AgentInstance for testing."""
    mock_instance = Mock(spec=AgentInstanceDTO)
    mock_instance.agent_class = "TestAgent"
    mock_instance.agent_id = "test_agent_1"
    mock_instance.agent_config = sample_agent_config
    return mock_instance


@pytest.fixture
def sample_agent_entity():
    """Create a sample AgentEntity for testing."""
    mock_entity = Mock()
    mock_entity.agent_class = "TestAgent"
    mock_entity.agent_id = "test_agent_1"
    mock_entity.name = LocaleString(en="Test Agent 1")
    mock_entity.description = LocaleString(en="A test agent")
    mock_entity.icon = "test-icon"
    return mock_entity


@pytest.fixture
def mock_nats():
    """Create a mock NATS connection."""
    return Mock()


@pytest.fixture
def mock_locale_handler():
    """Create a mock LocaleHandler."""
    return Mock(spec=LocaleHandler)


@pytest.fixture
def mock_user_identity():
    """Create a mock UserIdentity."""
    mock_user = Mock(spec=UserIdentity)
    mock_user.id = "user_123"
    return mock_user


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test."""
    DISCOVER_AGENTS_CACHE.clear()
    GET_AGENT_INSTANCE_CACHE.clear()
    GET_AGENT_CLASS_CACHE.clear()


class TestAgentServiceUnit:
    """Unit tests for AgentService methods."""

    def test_get_minimal_agent_success(self, sample_agent_entity, mock_locale_handler):
        """Test get_minimal_agent returns correct MinimalAgentDTO."""
        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = sample_agent_entity

            with patch.object(MinimalAgentDTO, "from_entity") as mock_from_entity:
                expected_dto = Mock(spec=MinimalAgentDTO)
                mock_from_entity.return_value = expected_dto

                result = AgentService.get_minimal_agent("TestAgent", "test_agent_1", mock_locale_handler)

                mock_get_agent.assert_called_once_with(agent_class="TestAgent", agent_id="test_agent_1")
                mock_from_entity.assert_called_once_with(sample_agent_entity, mock_locale_handler)
                assert result == expected_dto

    def test_get_minimal_agent_not_found(self, mock_locale_handler):
        """Test get_minimal_agent when agent not found."""
        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = None

            with patch.object(MinimalAgentDTO, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = None

                result = AgentService.get_minimal_agent("TestAgent", "nonexistent", mock_locale_handler)

                mock_get_agent.assert_called_once_with(agent_class="TestAgent", agent_id="nonexistent")
                mock_from_entity.assert_called_once_with(None, mock_locale_handler)
                assert result is None

    @pytest.mark.asyncio
    async def test_get_agent_success(self, mock_nats, sample_agent_entity, mock_locale_handler):
        """Test get_agent returns agent from database."""
        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = sample_agent_entity

            with patch.object(AgentDTO, "from_entity") as mock_from_entity:
                expected_dto = Mock(spec=AgentDTO)
                mock_from_entity.return_value = expected_dto

                result = await AgentService.get_agent(mock_nats, "TestAgent", "test_agent_1", mock_locale_handler)

                mock_get_agent.assert_called_once_with("TestAgent", "test_agent_1")
                mock_from_entity.assert_called_once_with(sample_agent_entity, mock_locale_handler)
                assert result == expected_dto

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, mock_nats, mock_locale_handler):
        """Test get_agent raises 404 when agent not found in database."""
        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await AgentService.get_agent(mock_nats, "TestAgent", "nonexistent", mock_locale_handler)

            assert exc_info.value.status_code == 404
            assert "Agent TestAgent.nonexistent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_agents_success(self, mock_nats, sample_agent_entity, mock_locale_handler):
        """Test get_agents returns all agents from database."""
        with patch.object(AgentEntity, "get_agents") as mock_get_agents:
            mock_get_agents.return_value = [sample_agent_entity]

            with patch.object(AgentDTO, "from_entity") as mock_from_entity:
                agent_dto = Mock(spec=AgentDTO)
                agent_dto.agent_id = "test_agent_1"
                agent_dto.agent_class = "TestAgent"
                mock_from_entity.return_value = agent_dto

                result = await AgentService.get_agents(mock_nats, mock_locale_handler)

                mock_get_agents.assert_called_once()
                mock_from_entity.assert_called_once_with(sample_agent_entity, mock_locale_handler)

                assert len(result) == 1
                assert agent_dto in result

    @pytest.mark.asyncio
    async def test_get_agents_multiple(self, mock_nats, sample_agent_entity, mock_locale_handler):
        """Test get_agents returns multiple agents from database."""
        second_entity = Mock()
        second_entity.agent_class = "TestAgent"
        second_entity.agent_id = "test_agent_2"

        with patch.object(AgentEntity, "get_agents") as mock_get_agents:
            mock_get_agents.return_value = [sample_agent_entity, second_entity]

            with patch.object(AgentDTO, "from_entity") as mock_from_entity:
                first_dto = Mock(spec=AgentDTO)
                first_dto.agent_id = "test_agent_1"
                first_dto.agent_class = "TestAgent"
                second_dto = Mock(spec=AgentDTO)
                second_dto.agent_id = "test_agent_2"
                second_dto.agent_class = "TestAgent"
                mock_from_entity.side_effect = [first_dto, second_dto]

                result = await AgentService.get_agents(mock_nats, mock_locale_handler)

                mock_get_agents.assert_called_once()
                assert mock_from_entity.call_count == 2

                assert len(result) == 2
                assert first_dto in result
                assert second_dto in result

    @pytest.mark.asyncio
    async def test_discover_agent_instances_success(self, mock_nats, sample_agent_class, sample_agent_config):
        """Test discover_agent_instances returns configured agents."""
        with patch.object(AgentService, "_discover_agent_classes") as mock_discover_classes:
            mock_discover_classes.return_value = [sample_agent_class]

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_config_doc = Mock()
                mock_config_doc.agent_id = "custom_agent"
                mock_find_configs.return_value = [mock_config_doc]

                with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                    custom_config = Mock(spec=AgentConfig)
                    custom_config.agent_id = "custom_agent"
                    mock_from_entity.return_value = custom_config

                    with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance1 = Mock(spec=AgentInstanceDTO)
                        mock_instance1.agent_id = "custom_agent"
                        mock_instance2 = Mock(spec=AgentInstanceDTO)
                        mock_instance2.agent_id = "test_agent_1"
                        mock_from_class_config.side_effect = [mock_instance1, mock_instance2]

                        with patch.object(mock_instance1, "create_or_update_agent_entity") as mock_1_create_update:
                            with patch.object(mock_instance2, "create_or_update_agent_entity") as mock_2_create_update:
                                result = await AgentService.discover_agent_instances(mock_nats)

                                mock_discover_classes.assert_called_once_with(mock_nats)
                                mock_find_configs.assert_called_once_with("TestAgent")
                                mock_from_entity.assert_called_once_with(mock_config_doc)
                                assert mock_from_class_config.call_count == 2
                                assert mock_1_create_update.call_count == 1
                                assert mock_2_create_update.call_count == 1

                                assert len(result) == 2
                                assert mock_instance1 in result
                                assert mock_instance2 in result

    @pytest.mark.asyncio
    async def test_discover_agent_instances_cached(self, mock_nats):
        """Test discover_agent_instances returns cached result."""
        cached_result = [Mock(spec=AgentInstanceDTO)]
        DISCOVER_AGENTS_CACHE["all_agent_instances"] = cached_result

        result = await AgentService.discover_agent_instances(mock_nats)

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_agent_classes_success(self, mock_nats):
        """Test _discover_agent_classes broadcasts discovery and returns results."""
        mock_response = Mock(spec=AgentClassDiscoveryResponseEvent)
        mock_response.agent_class = "TestAgent"
        mock_response.agent_config_specs = []
        mock_response.is_conversational = True
        mock_response.start_events = []
        mock_response.stop_events = []
        mock_response.default_agent_config = Mock()

        with patch("aihub_api.routes.agent.AgentService.AgentNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_agent_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.agent.AgentService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.agent.AgentService.AgentTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager.get_agent_class_discovery_subject_request.return_value = "test.subject"
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.agent.AgentService.sleep") as mock_sleep:
                        mock_sleep.return_value = None

                        with patch.object(AgentClassDTO, "from_discovery_event") as mock_from_event:
                            mock_agent_class = Mock(spec=AgentClassDTO)
                            mock_from_event.return_value = mock_agent_class

                            # Simulate receiving discovery response
                            original_start = mock_subscriber.start

                            async def mock_start_with_response():
                                await original_start()
                                # Simulate discovery handler being called
                                discovery_responses = [mock_response]
                                # Patch the discovery_responses list in the method
                                with patch(
                                    "aihub_api.routes.agent.AgentService.discovery_responses", discovery_responses
                                ):
                                    pass

                            # We need to patch the method's local discovery_responses
                            with patch("aihub_api.routes.agent.AgentService.ObjectId") as mock_objectid:
                                mock_objectid.return_value = "test_call_id"

                                # Mock the discovery_responses list within the method

                                async def patched_method(nc):
                                    # Simulate the original method logic but with our mock response
                                    discovery_responses = [mock_response]
                                    unique_agents_dict = {}

                                    for response in discovery_responses:
                                        unique_key = response.agent_class
                                        if unique_key not in unique_agents_dict:
                                            agent_class_dto = AgentClassDTO.from_discovery_event(response)
                                            unique_agents_dict[unique_key] = agent_class_dto

                                    agents = list(unique_agents_dict.values())
                                    if len(agents) > 0:
                                        DISCOVER_AGENTS_CACHE["all_agent_classes"] = agents
                                    return agents

                                with patch.object(AgentService, "_discover_agent_classes", patched_method):
                                    result = await AgentService._discover_agent_classes(mock_nats)

                                    assert len(result) == 1
                                    assert result[0] == mock_agent_class

    @pytest.mark.asyncio
    async def test_discover_agent_classes_cached(self, mock_nats):
        """Test _discover_agent_classes returns cached result."""
        cached_result = [Mock(spec=AgentClassDTO)]
        DISCOVER_AGENTS_CACHE["all_agent_classes"] = cached_result

        result = await AgentService._discover_agent_classes(mock_nats)

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_agent_class_success(self, mock_nats, sample_agent_config):
        """Test discover_agent_class returns specific agent class."""
        mock_response = Mock(spec=AgentClassDiscoveryResponseEvent)
        mock_response.agent_class = "TestAgent"
        mock_response.agent_config_specs = []
        mock_response.is_conversational = True
        mock_response.start_events = []
        mock_response.stop_events = []
        mock_response.default_agent_config = sample_agent_config

        with patch("aihub_api.routes.agent.AgentService.AgentNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_agent_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.agent.AgentService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.agent.AgentService.AgentClassTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager.get_agent_class_discovery_subject_request.return_value = "test.subject"
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.agent.AgentService.ObjectId") as mock_objectid:
                        mock_objectid.return_value = "test_call_id"

                        with patch("asyncio.wait_for") as mock_wait_for:
                            # Mock successful discovery
                            mock_event = Mock()
                            mock_event.wait = AsyncMock()
                            mock_event.set = Mock()

                            async def mock_wait_for_func(coro, timeout):
                                await coro
                                return True

                            mock_wait_for.side_effect = mock_wait_for_func

                            # Patch the discovery handler to simulate response

                            async def patched_method(nc, agent_class):
                                mock_agent_class = Mock()
                                mock_agent_class.agent_class = mock_response.agent_class
                                mock_agent_class.is_online = True
                                GET_AGENT_CLASS_CACHE[agent_class] = mock_agent_class
                                return mock_agent_class

                            with patch.object(AgentService, "_discover_agent_class", patched_method):
                                result = await AgentService._discover_agent_class(mock_nats, "TestAgent")

                                assert result.agent_class == "TestAgent"
                                assert result.is_online

    @pytest.mark.asyncio
    async def test_discover_agent_class_timeout(self, mock_nats):
        """Test discover_agent_class raises 404 on timeout."""
        with patch("aihub_api.routes.agent.AgentService.AgentNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_agent_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.agent.AgentService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.agent.AgentService.AgentClassTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.agent.AgentService.ObjectId") as mock_objectid:
                        mock_objectid.return_value = "test_call_id"

                        with patch("asyncio.wait_for") as mock_wait_for:
                            mock_wait_for.side_effect = TimeoutError()

                            with pytest.raises(HTTPException) as exc_info:
                                await AgentService._discover_agent_class(mock_nats, "TestAgent")

                            assert exc_info.value.status_code == 404
                            assert "Agent TestAgent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_agent_class_cached(self, mock_nats):
        """Test discover_agent_class returns cached result."""
        cached_result = Mock(spec=AgentClassDTO)
        GET_AGENT_CLASS_CACHE["TestAgent"] = cached_result

        result = await AgentService._discover_agent_class(mock_nats, "TestAgent")

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_send_event_success(self, mock_nats, mock_user_identity):
        """Test send_event successfully sends event to agent."""
        mock_event = Mock(spec=UserMessageEvent)
        mock_thread = Mock()
        mock_thread.id = ObjectId()
        mock_external_distributor = Mock()
        mock_stop_event = Mock()

        with patch.object(ThreadEntity, "get_thread_by_id") as mock_get_thread:
            mock_get_thread.return_value = mock_thread

            with patch("aihub_api.routes.agent.AgentService.ChatService") as mock_chat_service:
                mock_resources = Mock()
                mock_resources.stop_signal = Mock()
                mock_resources.stop_signal.wait = AsyncMock()
                mock_resources.subscriber = Mock()
                mock_resources.subscriber.stop = AsyncMock()
                mock_resources.stop_event = mock_stop_event

                mock_chat_service.start_json_event_interaction = AsyncMock(return_value=mock_resources)

                thread_id = ObjectId()
                result = await AgentService._send_event(
                    nc=mock_nats,
                    external_agent_event_distributor=mock_external_distributor,
                    user=mock_user_identity,
                    input_event=mock_event,
                    agent_class="TestAgent",
                    agent_id="test_agent_1",
                    thread_id=thread_id,
                )

                mock_get_thread.assert_called_once_with(str(thread_id))
                mock_chat_service.start_json_event_interaction.assert_called_once()
                mock_resources.stop_signal.wait.assert_called_once()
                mock_resources.subscriber.stop.assert_called_once()

                assert result == mock_stop_event

    @pytest.mark.asyncio
    async def test_send_event_creates_thread(self, mock_nats, mock_user_identity):
        """Test send_event creates new thread when thread_id is None."""
        mock_event = Mock(spec=UserMessageEvent)
        mock_thread = Mock()
        mock_thread.id = ObjectId()
        mock_external_distributor = Mock()
        mock_stop_event = Mock()

        with patch.object(ThreadEntity, "create_thread") as mock_create_thread:
            mock_create_thread.return_value = mock_thread

            with patch("aihub_api.routes.agent.AgentService.ChatService") as mock_chat_service:
                mock_resources = Mock()
                mock_resources.stop_signal = Mock()
                mock_resources.stop_signal.wait = AsyncMock()
                mock_resources.subscriber = Mock()
                mock_resources.subscriber.stop = AsyncMock()
                mock_resources.stop_event = mock_stop_event

                mock_chat_service.start_json_event_interaction = AsyncMock(return_value=mock_resources)

                result = await AgentService._send_event(
                    nc=mock_nats,
                    external_agent_event_distributor=mock_external_distributor,
                    user=mock_user_identity,
                    input_event=mock_event,
                    agent_class="TestAgent",
                    agent_id="test_agent_1",
                    thread_id=None,
                )

                mock_create_thread.assert_called_once()
                assert result == mock_stop_event

    @pytest.mark.asyncio
    async def test_get_paginated_agent_threads_success(self, mock_locale_handler):
        """Test get_paginated_agent_threads delegates to ThreadService."""
        mock_threads = [Mock(), Mock()]
        expected_total = 25

        with patch.object(ThreadService, "get_paginated_threads_for_agent") as mock_get_threads:
            mock_get_threads.return_value = (expected_total, mock_threads)

            total, threads = await AgentService.get_paginated_agent_threads(
                agent_class="TestAgent",
                agent_id="test_agent_1",
                t=mock_locale_handler,
                page=2,
                page_size=10,
                user_id="user_123",
            )

            mock_get_threads.assert_called_once_with(
                "TestAgent", "test_agent_1", t=mock_locale_handler, page=2, page_size=10, user_id="user_123"
            )

            assert total == expected_total
            assert threads == mock_threads

    def test_clear_cache_success(self):
        """Test clear_cache clears all caches."""
        # Clear caches first to ensure clean state
        AgentService._clear_cache()

        # Add some items to caches
        DISCOVER_AGENTS_CACHE["test"] = "value"
        GET_AGENT_INSTANCE_CACHE["test"] = "value"
        GET_AGENT_CLASS_CACHE["test"] = "value"

        # Verify caches have items
        assert len(DISCOVER_AGENTS_CACHE) > 0
        assert len(GET_AGENT_INSTANCE_CACHE) > 0
        assert len(GET_AGENT_CLASS_CACHE) > 0

        # Clear caches
        AgentService._clear_cache()

        # Verify caches are empty
        assert len(DISCOVER_AGENTS_CACHE) == 0
        assert len(GET_AGENT_INSTANCE_CACHE) == 0
        assert len(GET_AGENT_CLASS_CACHE) == 0

    @pytest.mark.asyncio
    async def test_get_agent_database_exception(self, mock_nats, mock_locale_handler):
        """Test get_agent handles database exceptions properly."""
        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                await AgentService.get_agent(mock_nats, "TestAgent", "test_agent_1", mock_locale_handler)

            assert str(exc_info.value) == "Database error"

    @pytest.mark.asyncio
    async def test_discover_agent_instances_no_results(self, mock_nats):
        """Test discover_agent_instances returns empty list when no agents found."""
        with patch.object(AgentService, "_discover_agent_classes") as mock_discover_classes:
            mock_discover_classes.return_value = []

            result = await AgentService.discover_agent_instances(mock_nats)

            assert result == []
            # Should not cache empty results
            assert "all_agent_instances" not in DISCOVER_AGENTS_CACHE

    @pytest.mark.asyncio
    async def test_discover_agent_classes_no_results(self, mock_nats):
        """Test _discover_agent_classes returns empty list when no agents respond."""
        with patch("aihub_api.routes.agent.AgentService.AgentNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_agent_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.agent.AgentService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.agent.AgentService.AgentTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.agent.AgentService.sleep") as mock_sleep:
                        mock_sleep.return_value = None

                        with patch("aihub_api.routes.agent.AgentService.ObjectId") as mock_objectid:
                            mock_objectid.return_value = "test_call_id"

                            # Mock empty discovery responses

                            async def patched_method(nc):
                                discovery_responses = []  # No responses
                                unique_agents_dict = {}

                                for response in discovery_responses:
                                    unique_key = response.agent_class
                                    if unique_key not in unique_agents_dict:
                                        agent_class_dto = AgentClassDTO.from_discovery_event(response)
                                        unique_agents_dict[unique_key] = agent_class_dto

                                agents = list(unique_agents_dict.values())
                                # Should not cache empty results
                                return agents

                            with patch.object(AgentService, "_discover_agent_classes", patched_method):
                                result = await AgentService._discover_agent_classes(mock_nats)

                                assert result == []
                                # Should not cache empty results
                                assert "all_agent_classes" not in DISCOVER_AGENTS_CACHE


class TestUpdateAgentConfiguration:
    """Unit tests for AgentService.update_agent_configuration method."""

    @pytest.mark.asyncio
    async def test_update_agent_configuration_warns_on_unknown_fields(self, caplog):
        """Test that update_agent_configuration logs a warning for unknown fields but still saves."""
        # Create a mock agent entity with form specs
        mock_agent_entity = Mock()
        mock_agent_entity.agent_class = "TestAgent"
        mock_agent_entity.agent_id = "test_agent_1"

        # Create mock form elements with names
        mock_form_element = Mock()
        mock_form_element.name = "valid_field"

        mock_config_specs = Mock()
        mock_config_specs.form = [mock_form_element]
        mock_config_specs.form_elements = [mock_form_element]
        mock_config_specs.name = LocaleString(en="Test")
        mock_config_specs.description = LocaleString(en="Test description")
        mock_config_specs.icon = "test-icon"

        mock_agent_entity.agent_config_specs = mock_config_specs

        mock_config_entity = Mock()
        mock_config_entity.config_data = {}
        mock_config_entity.save = Mock()

        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = mock_agent_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find_config:
                mock_find_config.return_value = mock_config_entity

                with patch.object(AgentService, "_clear_cache"):
                    # Update with an unknown field - should succeed with warning
                    await AgentService.update_agent_configuration(
                        agent_class="TestAgent",
                        agent_id="test_agent_1",
                        configuration={"invalid_field_that_does_not_exist": "value"},
                    )

                    # Verify the config was saved (unknown fields are preserved)
                    mock_config_entity.save.assert_called_once()
                    assert "invalid_field_that_does_not_exist" in mock_config_entity.config_data

                    # Verify warning was logged
                    assert "unknown fields" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_update_agent_configuration_clears_cache(self):
        """Test that update_agent_configuration clears the cache after update."""
        # Create a mock agent entity
        mock_agent_entity = Mock()
        mock_agent_entity.agent_class = "TestAgent"
        mock_agent_entity.agent_id = "test_agent_1"
        mock_agent_entity.agent_config_specs = None  # No form validation

        mock_config_entity = Mock()
        mock_config_entity.config_data = {}
        mock_config_entity.save = Mock()

        with patch.object(AgentEntity, "get_agent") as mock_get_agent:
            mock_get_agent.return_value = mock_agent_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find_config:
                mock_find_config.return_value = mock_config_entity

                with patch.object(AgentService, "_clear_cache") as mock_clear_cache:
                    await AgentService.update_agent_configuration(
                        agent_class="TestAgent",
                        agent_id="test_agent_1",
                        configuration={"name": {"en": "Updated Name"}},
                    )

                    # Verify cache was cleared
                    mock_clear_cache.assert_called_once()
