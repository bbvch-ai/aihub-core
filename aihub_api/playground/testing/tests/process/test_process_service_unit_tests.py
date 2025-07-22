from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery import ProcessClassDiscoveryResponseEvent
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.logging.logger import enable_logging
from fastapi import HTTPException

from aihub_api.routes.process.dto.MinimalProcessDTO import MinimalProcessDTO
from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.ProcessService import (
    DISCOVER_PROCESSES_CACHE,
    GET_PROCESS_CLASS_CACHE,
    GET_PROCESS_INSTANCE_CACHE,
    ProcessService,
)

enable_logging()


@pytest.fixture
def sample_process_config():
    """Create a sample ProcessConfig for testing."""
    return ProcessConfig(
        process_class="TestProcess",
        process_id="test_process_1",
        name=LocaleString(en="Test Process 1"),
        description=LocaleString(en="A test process for validation"),
        icon="test-icon",
    )


@pytest.fixture
def sample_process_class(sample_process_config):
    """Create a sample ProcessClass for testing."""
    mock_process_class = Mock(spec=ProcessClassDTO)
    mock_process_class.process_class = "TestProcess"
    mock_process_class.default_process_config = sample_process_config
    mock_process_class.process_config_specs = []
    mock_process_class.human_inputs = []
    mock_process_class.program_inputs = []
    mock_process_class.agent_inputs = []
    mock_process_class.is_online = True
    return mock_process_class


@pytest.fixture
def sample_process_instance(sample_process_class, sample_process_config):
    """Create a sample ProcessInstance for testing."""
    mock_instance = Mock(spec=ProcessInstanceDTO)
    mock_instance.process_class = "TestProcess"
    mock_instance.process_id = "test_process_1"
    mock_instance.process_config = sample_process_config
    return mock_instance


@pytest.fixture
def sample_process_entity():
    """Create a sample ProcessEntity for testing."""
    mock_entity = Mock()
    mock_entity.process_class = "TestProcess"
    mock_entity.process_id = "test_process_1"
    mock_entity.name = LocaleString(en="Test Process 1")
    mock_entity.description = LocaleString(en="A test process")
    mock_entity.icon = "test-icon"
    return mock_entity


@pytest.fixture
def mock_locale_handler():
    """Create a mock LocaleHandler for testing."""
    mock_handler = Mock(spec=LocaleHandler)
    mock_handler.extract.return_value = "Test Process"
    return mock_handler


class TestProcessServiceUnitTests:
    """Unit tests for ProcessService functionality."""

    def test_get_minimal_process_success(self, sample_process_entity, mock_locale_handler):
        """Test get_minimal_process returns correct MinimalProcessDTO."""
        sample_config = ProcessConfig(
            process_class="TestProcess",
            process_id="test_process_1",
            name=LocaleString(en="Test Process"),
            description=LocaleString(en="Test description"),
            icon="test-icon",
        )

        with patch.object(ProcessEntity, "get_process") as mock_get_process:
            mock_get_process.return_value = sample_process_entity

            with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = sample_config

                with patch("aihub_api.routes.process.ProcessService.ProcessConfigDTO") as mock_config_dto_class:
                    mock_config_dto = Mock()
                    mock_config_dto_class.from_process_config.return_value = mock_config_dto

                    result = ProcessService.get_minimal_process("TestProcess", "test_process_1", mock_locale_handler)

                    mock_get_process.assert_called_once_with(process_class="TestProcess", process_id="test_process_1")
                    mock_from_entity.assert_called_once_with(
                        sample_process_entity.process_config or sample_process_entity.default_process_config
                    )
                    assert isinstance(result, MinimalProcessDTO)
                    assert result.process_class == "TestProcess"
                    assert result.process_id == "test_process_1"

    def test_get_minimal_process_not_found(self, mock_locale_handler):
        """Test get_minimal_process when process not found."""
        with patch.object(ProcessEntity, "get_process") as mock_get_process:
            mock_get_process.return_value = None

            with pytest.raises(AttributeError):
                ProcessService.get_minimal_process("TestProcess", "nonexistent", mock_locale_handler)

    @pytest.mark.asyncio
    async def test_get_process_online_success(self, sample_process_instance, mock_locale_handler):
        """Test get_process returns online process when discoverable."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.return_value = sample_process_instance

            with patch.object(ProcessDTO, "from_instance") as mock_from_instance:
                mock_dto = Mock()
                mock_from_instance.return_value = mock_dto

                result = await ProcessService.get_process(Mock(), "TestProcess", "test_process_1", mock_locale_handler)

                mock_discover.assert_called_once_with(Mock(), "TestProcess", "test_process_1")
                mock_from_instance.assert_called_once_with(
                    sample_process_instance, is_online=True, t=mock_locale_handler
                )
                assert result == mock_dto

    @pytest.mark.asyncio
    async def test_get_process_falls_back_to_database(self, sample_process_entity, mock_locale_handler):
        """Test get_process falls back to database when process not discoverable."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.side_effect = HTTPException(status_code=404, detail="Process not found")

            with patch.object(ProcessEntity, "get_process") as mock_get_process:
                mock_get_process.return_value = sample_process_entity

                with patch.object(ProcessDTO, "from_entity") as mock_from_entity:
                    mock_dto = Mock()
                    mock_from_entity.return_value = mock_dto

                    result = await ProcessService.get_process(
                        Mock(), "TestProcess", "test_process_1", mock_locale_handler
                    )

                    mock_get_process.assert_called_once_with("TestProcess", "test_process_1")
                    mock_from_entity.assert_called_once_with(
                        sample_process_entity, mock_locale_handler, is_online=False
                    )
                    assert result == mock_dto

    @pytest.mark.asyncio
    async def test_get_process_not_found_anywhere(self, mock_locale_handler):
        """Test get_process raises 404 when process not found online or in database."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.side_effect = HTTPException(status_code=404, detail="Process not found")

            with patch.object(ProcessEntity, "get_process") as mock_get_process:
                mock_get_process.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.get_process(Mock(), "TestProcess", "nonexistent", mock_locale_handler)

                assert exc_info.value.status_code == 404
                assert "Process TestProcess.nonexistent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_processes_combines_online_and_saved(
        self, sample_process_instance, sample_process_entity, mock_locale_handler
    ):
        """Test get_processes returns both online and saved processes."""
        online_dto = Mock()
        online_dto.process_id = "online_process"
        online_dto.process_class = "TestProcess"

        saved_dto = Mock()
        saved_dto.process_id = "saved_process"
        saved_dto.process_class = "TestProcess"

        with patch.object(ProcessService, "discover_processes") as mock_discover:
            mock_discover.return_value = [online_dto]

            with patch.object(ProcessEntity, "get_processes") as mock_get_processes:
                mock_get_processes.return_value = [sample_process_entity]

                with patch.object(ProcessDTO, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = saved_dto

                    result = await ProcessService.get_processes(Mock(), mock_locale_handler)

                    # Should include both online and saved processes (no duplicates)
                    assert len(result) == 2
                    assert online_dto in result
                    assert saved_dto in result

    @pytest.mark.asyncio
    async def test_discover_process_class_success(self, sample_process_class):
        """Test discover_process_class successfully discovers and caches process class."""
        mock_nc = AsyncMock()
        mock_event = Mock(spec=ProcessClassDiscoveryResponseEvent)

        # Clear cache first
        GET_PROCESS_CLASS_CACHE.clear()

        with patch.object(ProcessClassDTO, "from_discovery_event") as mock_from_event:
            mock_from_event.return_value = sample_process_class

            with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
                mock_subscriber = AsyncMock()
                mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

                # Mock the handler to simulate receiving a response
                async def mock_handler_side_effect(*args, **kwargs):
                    handler = args[2] if len(args) > 2 else kwargs.get("handler")
                    if handler:
                        await handler(mock_event, Mock())

                mock_subscriber.start.side_effect = mock_handler_side_effect

                with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                    mock_publisher = AsyncMock()
                    mock_publisher_class.return_value = mock_publisher

                    with patch("asyncio.wait_for") as mock_wait_for:
                        mock_wait_for.return_value = None  # Simulate successful wait

                        result = await ProcessService.discover_process_class(mock_nc, "TestProcess")

                        assert result == sample_process_class
                        assert GET_PROCESS_CLASS_CACHE["TestProcess"] == sample_process_class

    @pytest.mark.asyncio
    async def test_discover_process_class_timeout(self):
        """Test discover_process_class raises HTTPException on timeout."""
        mock_nc = AsyncMock()

        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber = AsyncMock()
            mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                mock_publisher = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("asyncio.wait_for") as mock_wait_for:
                    mock_wait_for.side_effect = TimeoutError()

                    with pytest.raises(HTTPException) as exc_info:
                        await ProcessService.discover_process_class(mock_nc, "TestProcess")

                    assert exc_info.value.status_code == 404
                    assert "Process TestProcess not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_processes_converts_instances_to_dtos(self, sample_process_instance, mock_locale_handler):
        """Test discover_processes converts process instances to DTOs."""
        with patch.object(ProcessService, "discover_process_instances") as mock_discover_instances:
            mock_discover_instances.return_value = [sample_process_instance]

            with patch.object(ProcessDTO, "from_instance") as mock_from_instance:
                mock_dto = Mock()
                mock_from_instance.return_value = mock_dto

                result = await ProcessService.discover_processes(Mock(), mock_locale_handler)

                assert len(result) == 1
                assert result[0] == mock_dto
                mock_from_instance.assert_called_once_with(
                    sample_process_instance, is_online=True, t=mock_locale_handler
                )

    def test_clear_cache_clears_all_caches(self):
        """Test clear_cache method clears all process-related caches."""
        # Populate all caches
        DISCOVER_PROCESSES_CACHE["test_key"] = Mock()
        GET_PROCESS_INSTANCE_CACHE[("TestProcess", "test_id")] = Mock()
        GET_PROCESS_CLASS_CACHE["TestProcess"] = Mock()

        # Verify caches have data
        assert len(DISCOVER_PROCESSES_CACHE) > 0
        assert len(GET_PROCESS_INSTANCE_CACHE) > 0
        assert len(GET_PROCESS_CLASS_CACHE) > 0

        # Clear caches
        ProcessService.clear_cache()

        # Verify all caches are cleared
        assert len(DISCOVER_PROCESSES_CACHE) == 0
        assert len(GET_PROCESS_INSTANCE_CACHE) == 0
        assert len(GET_PROCESS_CLASS_CACHE) == 0

    @pytest.mark.asyncio
    async def test_discover_process_classes_caching_behavior(self, sample_process_class):
        """Test that discover_process_classes properly caches results."""
        cache_key = "all_process_classes"

        # Clear cache first
        DISCOVER_PROCESSES_CACHE.clear()

        mock_nc = AsyncMock()
        mock_event = Mock(spec=ProcessClassDiscoveryResponseEvent)
        mock_event.process_class = "TestProcess"

        with patch.object(ProcessClassDTO, "from_discovery_event") as mock_from_event:
            mock_from_event.return_value = sample_process_class

            with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
                mock_subscriber = AsyncMock()
                mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

                responses = []

                async def capture_handler(*args, **kwargs):
                    handler = args[2] if len(args) > 2 else kwargs.get("handler")
                    if handler:
                        responses.append(mock_event)
                        await handler(mock_event, Mock())

                mock_subscriber.start.side_effect = capture_handler

                with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                    mock_publisher = AsyncMock()
                    mock_publisher_class.return_value = mock_publisher

                    with patch("asyncio.sleep") as mock_sleep:
                        mock_sleep.return_value = None

                        # First call should populate cache
                        result1 = await ProcessService.discover_process_classes(mock_nc)
                        assert len(result1) == 1
                        assert cache_key in DISCOVER_PROCESSES_CACHE

                        # Second call should use cache
                        result2 = await ProcessService.discover_process_classes(mock_nc)
                        assert result2 == DISCOVER_PROCESSES_CACHE[cache_key]
                        assert len(result2) == 1

    @pytest.mark.asyncio
    async def test_process_service_error_handling_during_discovery(self):
        """Test ProcessService handles errors gracefully during discovery operations."""
        mock_nc = AsyncMock()

        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber_class.for_process_class_discovery_response_events.side_effect = Exception("NATS error")

            with pytest.raises(Exception) as exc_info:
                await ProcessService.discover_process_class(mock_nc, "TestProcess")

            assert str(exc_info.value) == "NATS error"

    @pytest.mark.asyncio
    async def test_multiple_process_configs_handling(self, sample_process_class):
        """Test handling of multiple process configurations for the same class."""
        config1 = ProcessConfig(
            process_class="TestProcess",
            process_id="process_1",
            name=LocaleString(en="Process 1"),
            description=LocaleString(en="First process"),
            icon="icon1",
        )

        config2 = ProcessConfig(
            process_class="TestProcess",
            process_id="process_2",
            name=LocaleString(en="Process 2"),
            description=LocaleString(en="Second process"),
            icon="icon2",
        )

        mock_doc1 = Mock()
        mock_doc1.process_id = "process_1"
        mock_doc2 = Mock()
        mock_doc2.process_id = "process_2"

        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_doc1, mock_doc2]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.side_effect = [config1, config2]

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                        mock_instance1 = Mock()
                        mock_instance1.process_id = "process_1"
                        mock_instance2 = Mock()
                        mock_instance2.process_id = "process_2"

                        mock_create_instance.side_effect = [mock_instance1, mock_instance2]

                        # Test discovering specific process
                        result1 = await ProcessService.discover_process_instance(Mock(), "TestProcess", "process_1")
                        assert result1 == mock_instance1

                        # Reset mocks for second call
                        mock_from_entity.side_effect = [config1, config2]
                        mock_create_instance.side_effect = [mock_instance1, mock_instance2]

                        result2 = await ProcessService.discover_process_instance(Mock(), "TestProcess", "process_2")
                        assert result2 == mock_instance2

                        # Verify correct configs were used
                        assert mock_from_entity.call_count >= 2
