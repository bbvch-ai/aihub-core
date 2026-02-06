from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from bson import ObjectId
from fastapi import HTTPException

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.agent.dto.FullAgentInstanceDTO import FullAgentInstanceDTO
from aihub_api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO
from aihub_api.routes.thread.ThreadService import ThreadService

enable_logging()


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
def sample_agent_class_entity():
    """Create a sample AgentClassEntity for testing (class-level data only, no agent_id)."""
    mock_entity = Mock()
    mock_entity.agent_class = "TestAgent"
    mock_entity.name = LocaleString(en="Test Agent 1")
    mock_entity.description = LocaleString(en="A test agent")
    mock_entity.icon = "test-icon"
    mock_entity.is_conversational = True
    mock_entity.start_events = []
    mock_entity.stop_events = []
    mock_entity.hitl_request_events = []
    mock_entity.hitl_response_events = []
    mock_entity.network_graph = {}
    mock_entity.form = []
    mock_entity.is_online = True
    return mock_entity


@pytest.fixture
def sample_config_entity():
    """Create a sample AgentConfigEntityDocument for testing (instance-level data with agent_id)."""
    mock_entity = Mock()
    mock_entity.agent_class = "TestAgent"
    mock_entity.agent_id = "test_agent_1"
    mock_entity.name = LocaleString(en="Test Agent 1")
    mock_entity.description = LocaleString(en="A test agent instance")
    mock_entity.icon = "test-icon"
    mock_entity.configuration = {}
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


class TestAgentServiceUnit:
    """Unit tests for AgentService methods."""

    def test_get_minimal_agent_instance_success(
        self, sample_agent_class_entity, sample_config_entity, mock_locale_handler
    ):
        """Test get_minimal_agent_instance returns correct MinimalAgentInstanceDTO."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = sample_agent_class_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_get_config:
                mock_get_config.return_value = sample_config_entity

                with patch.object(MinimalAgentInstanceDTO, "from_class_and_config") as mock_from:
                    expected_dto = Mock(spec=MinimalAgentInstanceDTO)
                    mock_from.return_value = expected_dto

                    result = AgentService.get_minimal_agent_instance("TestAgent", "test_agent_1", mock_locale_handler)

                    mock_get_class.assert_called_once()
                    mock_get_config.assert_called_once()
                    mock_from.assert_called_once_with(
                        sample_agent_class_entity, sample_config_entity, mock_locale_handler
                    )
                    assert result == expected_dto

    def test_get_minimal_agent_instance_class_not_found(self, mock_locale_handler):
        """Test get_minimal_agent_instance when agent class not found."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                AgentService.get_minimal_agent_instance("TestAgent", "nonexistent", mock_locale_handler)

            assert exc_info.value.status_code == 404
            assert "Agent class TestAgent not found" in str(exc_info.value.detail)

    def test_get_minimal_agent_instance_config_not_found(self, sample_agent_class_entity, mock_locale_handler):
        """Test get_minimal_agent_instance when agent config not found."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = sample_agent_class_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_get_config:
                mock_get_config.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    AgentService.get_minimal_agent_instance("TestAgent", "nonexistent", mock_locale_handler)

                assert exc_info.value.status_code == 404
                assert "Agent config TestAgent/nonexistent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_agent_instance_success(
        self, sample_agent_class_entity, sample_config_entity, mock_locale_handler
    ):
        """Test get_agent_instance returns agent from database."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = sample_agent_class_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_get_config:
                mock_get_config.return_value = sample_config_entity

                with patch.object(FullAgentInstanceDTO, "from_class_and_config") as mock_from:
                    expected_dto = Mock(spec=FullAgentInstanceDTO)
                    mock_from.return_value = expected_dto

                    result = await AgentService.get_agent_instance("TestAgent", "test_agent_1", mock_locale_handler)

                    mock_get_class.assert_called_once_with("TestAgent")
                    mock_get_config.assert_called_once_with("TestAgent", "test_agent_1")
                    mock_from.assert_called_once_with(
                        sample_agent_class_entity, sample_config_entity, mock_locale_handler
                    )
                    assert result == expected_dto

    @pytest.mark.asyncio
    async def test_get_agent_instance_class_not_found(self, mock_locale_handler):
        """Test get_agent_instance raises 404 when agent class not found in database."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await AgentService.get_agent_instance("TestAgent", "nonexistent", mock_locale_handler)

            assert exc_info.value.status_code == 404
            assert "Agent class TestAgent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_agent_instance_config_not_found(self, sample_agent_class_entity, mock_locale_handler):
        """Test get_agent_instance raises 404 when agent config not found in database."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.return_value = sample_agent_class_entity

            with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_get_config:
                mock_get_config.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await AgentService.get_agent_instance("TestAgent", "nonexistent", mock_locale_handler)

                assert exc_info.value.status_code == 404
                assert "Agent instance TestAgent/nonexistent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_all_agent_instances_success(
        self, sample_agent_class_entity, sample_config_entity, mock_locale_handler
    ):
        """Test get_all_agent_instances returns all agents from database."""
        with patch.object(AgentClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [sample_agent_class_entity]

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_get_configs:
                mock_get_configs.return_value = [sample_config_entity]

                with patch.object(FullAgentInstanceDTO, "from_class_and_config") as mock_from:
                    agent_dto = Mock(spec=FullAgentInstanceDTO)
                    agent_dto.agent_id = "test_agent_1"
                    agent_dto.agent_class = "TestAgent"
                    mock_from.return_value = agent_dto

                    result = await AgentService.get_all_agent_instances(mock_locale_handler)

                    mock_get_all.assert_called_once()
                    assert len(result) == 1
                    assert agent_dto in result

    @pytest.mark.asyncio
    async def test_get_all_agent_instances_multiple(
        self, sample_agent_class_entity, sample_config_entity, mock_locale_handler
    ):
        """Test get_all_agent_instances returns multiple agents from database."""
        second_config = Mock()
        second_config.agent_class = "TestAgent"
        second_config.agent_id = "test_agent_2"

        with patch.object(AgentClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [sample_agent_class_entity]

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_get_configs:
                mock_get_configs.return_value = [sample_config_entity, second_config]

                with patch.object(FullAgentInstanceDTO, "from_class_and_config") as mock_from:
                    first_dto = Mock(spec=FullAgentInstanceDTO)
                    first_dto.agent_id = "test_agent_1"
                    first_dto.agent_class = "TestAgent"
                    second_dto = Mock(spec=FullAgentInstanceDTO)
                    second_dto.agent_id = "test_agent_2"
                    second_dto.agent_class = "TestAgent"
                    mock_from.side_effect = [first_dto, second_dto]

                    result = await AgentService.get_all_agent_instances(mock_locale_handler)

                    mock_get_all.assert_called_once()
                    assert mock_from.call_count == 2

                    assert len(result) == 2
                    assert first_dto in result
                    assert second_dto in result

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
    async def test_get_agent_instance_threads_success(self, mock_locale_handler):
        """Test get_agent_instance_threads delegates to ThreadService."""
        mock_threads = [Mock(), Mock()]
        expected_total = 25

        with patch.object(ThreadService, "get_paginated_threads_for_agent") as mock_get_threads:
            mock_get_threads.return_value = (expected_total, mock_threads)

            total, threads = await AgentService.get_agent_instance_threads(
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

    @pytest.mark.asyncio
    async def test_get_agent_instance_database_exception(self, mock_locale_handler):
        """Test get_agent_instance handles database exceptions properly."""
        with patch.object(AgentClassEntity, "get_by_agent_class") as mock_get_class:
            mock_get_class.side_effect = Exception("Database error")

            with pytest.raises(Exception) as exc_info:
                await AgentService.get_agent_instance("TestAgent", "test_agent_1", mock_locale_handler)

            assert str(exc_info.value) == "Database error"
