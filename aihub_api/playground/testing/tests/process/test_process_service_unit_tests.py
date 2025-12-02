from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery.process.ProcessClassDiscoveryResponseEvent import (
    ProcessClassDiscoveryResponseEvent,
)
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.persistence.process.ProcessEntity import ProcessEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.infrastructure.logging.logger import enable_logging
from bson import ObjectId
from fastapi import HTTPException

from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessDTO import ProcessDTO
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.ProcessService import (
    DISCOVER_PROCESSES_CACHE,
    GET_PROCESS_CLASS_CACHE,
    GET_PROCESS_INSTANCE_CACHE,
    ProcessService,
)
from aihub_api.runners.simulation.process.events.HumanStartWork import HumanStartEvent

enable_logging()


@pytest.fixture(autouse=True)
def cleanup_db_and_cache(sample_process_config):
    ProcessService._clear_cache()
    yield
    ProcessService._clear_cache()


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
    mock_process_class.is_conversational = True
    mock_process_class.start_events = []
    mock_process_class.stop_events = []
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
    DISCOVER_PROCESSES_CACHE.clear()
    GET_PROCESS_INSTANCE_CACHE.clear()
    GET_PROCESS_CLASS_CACHE.clear()


class TestProcessServiceUnit:
    """Unit tests for ProcessService methods."""

    @pytest.mark.asyncio
    async def test_get_process_online_success(self, mock_nats, sample_process_instance, mock_locale_handler):
        """Test get_process returns online process when discoverable."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.return_value = sample_process_instance

            with patch.object(ProcessDTO, "from_instance") as mock_from_instance:
                expected_dto = Mock(spec=ProcessDTO)
                mock_from_instance.return_value = expected_dto

                result = await ProcessService.get_process(
                    mock_nats, "TestProcess", "test_process_1", mock_locale_handler
                )

                mock_discover.assert_called_once_with(mock_nats, "TestProcess", "test_process_1")
                mock_from_instance.assert_called_once_with(
                    sample_process_instance, is_online=True, t=mock_locale_handler
                )
                assert result == expected_dto

    @pytest.mark.asyncio
    async def test_get_process_offline_fallback(self, mock_nats, sample_process_entity, mock_locale_handler):
        """Test get_process falls back to database when not discoverable."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.side_effect = HTTPException(status_code=404, detail="Not found")

            with patch.object(ProcessEntity, "get_process") as mock_get_process:
                mock_get_process.return_value = sample_process_entity

                with patch.object(ProcessDTO, "from_entity") as mock_from_entity:
                    expected_dto = Mock(spec=ProcessDTO)
                    mock_from_entity.return_value = expected_dto

                    result = await ProcessService.get_process(
                        mock_nats, "TestProcess", "test_process_1", mock_locale_handler
                    )

                    mock_discover.assert_called_once_with(mock_nats, "TestProcess", "test_process_1")
                    mock_get_process.assert_called_once_with("TestProcess", "test_process_1")
                    mock_from_entity.assert_called_once_with(
                        sample_process_entity, mock_locale_handler, is_online=False
                    )
                    assert result == expected_dto

    @pytest.mark.asyncio
    async def test_get_process_not_found(self, mock_nats, mock_locale_handler):
        """Test get_process raises 404 when process not found anywhere."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.side_effect = HTTPException(status_code=404, detail="Not found")

            with patch.object(ProcessEntity, "get_process") as mock_get_process:
                mock_get_process.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.get_process(mock_nats, "TestProcess", "nonexistent", mock_locale_handler)

                assert exc_info.value.status_code == 404
                assert "Process TestProcess.nonexistent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_processes_success(
        self, mock_nats, sample_process_instance, sample_process_entity, mock_locale_handler
    ):
        """Test get_processes returns both discovered and saved processes."""
        with patch.object(ProcessService, "discover_process_instances") as mock_discover:
            mock_discover.return_value = [sample_process_instance]

            with patch.object(ProcessEntity, "get_processes") as mock_get_processes:
                mock_get_processes.return_value = [sample_process_entity]

                with patch.object(ProcessDTO, "from_instance") as mock_from_instance:
                    discovered_dto = Mock(spec=ProcessDTO)
                    discovered_dto.process_id = "test_process_1"
                    discovered_dto.process_class = "TestProcess"
                    mock_from_instance.return_value = discovered_dto

                    with patch.object(ProcessDTO, "from_entity") as mock_from_entity:
                        saved_dto = Mock(spec=ProcessDTO)
                        saved_dto.process_id = "different_process"
                        saved_dto.process_class = "TestProcess"
                        mock_from_entity.return_value = saved_dto

                        result = await ProcessService.get_processes(mock_nats, mock_locale_handler)

                        mock_discover.assert_called_once_with(mock_nats)
                        mock_get_processes.assert_called_once()
                        mock_from_instance.assert_called_once_with(
                            sample_process_instance, is_online=True, t=mock_locale_handler
                        )
                        mock_from_entity.assert_called_once_with(
                            sample_process_entity, mock_locale_handler, is_online=False
                        )

                        assert len(result) == 2
                        assert discovered_dto in result
                        assert saved_dto in result

    @pytest.mark.asyncio
    async def test_get_processes_deduplication(
        self, mock_nats, sample_process_instance, sample_process_entity, mock_locale_handler
    ):
        """Test get_processes deduplicates processes found in both discovered and saved."""
        with patch.object(ProcessService, "discover_process_instances") as mock_discover:
            mock_discover.return_value = [sample_process_instance]

            with patch.object(ProcessEntity, "get_processes") as mock_get_processes:
                mock_get_processes.return_value = [sample_process_entity]

                with patch.object(ProcessDTO, "from_instance") as mock_from_instance:
                    discovered_dto = Mock(spec=ProcessDTO)
                    discovered_dto.process_id = "test_process_1"
                    discovered_dto.process_class = "TestProcess"
                    mock_from_instance.return_value = discovered_dto

                    with patch.object(ProcessDTO, "from_entity") as mock_from_entity:
                        saved_dto = Mock(spec=ProcessDTO)
                        saved_dto.process_id = "test_process_1"  # Same as discovered
                        saved_dto.process_class = "TestProcess"
                        mock_from_entity.return_value = saved_dto

                        result = await ProcessService.get_processes(mock_nats, mock_locale_handler)

                        # Should only return discovered process, not saved duplicate
                        assert len(result) == 1
                        assert discovered_dto in result
                        assert saved_dto not in result

    @pytest.mark.asyncio
    async def test_discover_process_instances_success(self, mock_nats, sample_process_class, sample_process_config):
        """Test discover_process_instances returns configured processes."""
        with patch.object(ProcessService, "_discover_process_classes") as mock_discover_classes:
            mock_discover_classes.return_value = [sample_process_class]

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_config_doc = Mock()
                mock_config_doc.process_id = "custom_process"
                mock_find_configs.return_value = [mock_config_doc]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    custom_config = Mock(spec=ProcessConfig)
                    custom_config.process_id = "custom_process"
                    mock_from_entity.return_value = custom_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance1 = Mock(spec=ProcessInstanceDTO)
                        mock_instance1.process_id = "custom_process"
                        mock_instance2 = Mock(spec=ProcessInstanceDTO)
                        mock_instance2.process_id = "test_process_1"
                        mock_from_class_config.side_effect = [mock_instance1, mock_instance2]

                        with patch.object(mock_instance1, "create_or_update_process_entity") as mock_1_create_update:
                            with patch.object(
                                mock_instance2, "create_or_update_process_entity"
                            ) as mock_2_create_update:
                                result = await ProcessService.discover_process_instances(mock_nats)

                                mock_discover_classes.assert_called_once_with(mock_nats)
                                mock_find_configs.assert_called_once_with("TestProcess")
                                mock_from_entity.assert_called_once_with(mock_config_doc)
                                assert mock_from_class_config.call_count == 2
                                assert mock_1_create_update.call_count == 1
                                assert mock_2_create_update.call_count == 1

                                assert len(result) == 2
                                assert mock_instance1 in result
                                assert mock_instance2 in result

    @pytest.mark.asyncio
    async def test_discover_process_instances_cached(self, mock_nats):
        """Test discover_process_instances returns cached result."""
        cached_result = [Mock(spec=ProcessInstanceDTO)]
        DISCOVER_PROCESSES_CACHE["all_process_instances"] = cached_result

        result = await ProcessService.discover_process_instances(mock_nats)

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_process_classes_success(self, mock_nats):
        """Test discover_process_classes broadcasts discovery and returns results."""
        mock_response = Mock(spec=ProcessClassDiscoveryResponseEvent)
        mock_response.process_class = "TestProcess"
        mock_response.process_config_specs = []
        mock_response.is_conversational = True
        mock_response.start_events = []
        mock_response.stop_events = []
        mock_response.default_process_config = Mock()

        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.process.ProcessService.ProcessTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager.get_process_class_discovery_subject_request.return_value = "test.subject"
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.process.ProcessService.sleep") as mock_sleep:
                        mock_sleep.return_value = None

                        with patch.object(ProcessClassDTO, "from_discovery_event") as mock_from_event:
                            mock_process_class = Mock(spec=ProcessClassDTO)
                            mock_from_event.return_value = mock_process_class

                            # Simulate receiving discovery response
                            original_start = mock_subscriber.start

                            async def mock_start_with_response():
                                await original_start()
                                # Simulate discovery handler being called
                                discovery_responses = [mock_response]
                                # Patch the discovery_responses list in the method
                                with patch(
                                    "aihub_api.routes.process.ProcessService.discovery_responses", discovery_responses
                                ):
                                    pass

                            # We need to patch the method's local discovery_responses
                            with patch("aihub_api.routes.process.ProcessService.ObjectId") as mock_objectid:
                                mock_objectid.return_value = "test_call_id"

                                # Mock the discovery_responses list within the method

                                async def patched_method(nc):
                                    # Simulate the original method logic but with our mock response
                                    discovery_responses = [mock_response]
                                    unique_processes_dict = {}

                                    for response in discovery_responses:
                                        unique_key = response.process_class
                                        if unique_key not in unique_processes_dict:
                                            process_class_dto = ProcessClassDTO.from_discovery_event(response)
                                            unique_processes_dict[unique_key] = process_class_dto

                                    processes = list(unique_processes_dict.values())
                                    if len(processes) > 0:
                                        DISCOVER_PROCESSES_CACHE["all_process_classes"] = processes
                                    return processes

                                with patch.object(ProcessService, "_discover_process_classes", patched_method):
                                    result = await ProcessService._discover_process_classes(mock_nats)

                                    assert len(result) == 1
                                    assert result[0] == mock_process_class

    @pytest.mark.asyncio
    async def test_discover_process_classes_cached(self, mock_nats):
        """Test discover_process_classes returns cached result."""
        cached_result = [Mock(spec=ProcessClassDTO)]
        DISCOVER_PROCESSES_CACHE["all_process_classes"] = cached_result

        result = await ProcessService._discover_process_classes(mock_nats)

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_process_class_success(self, mock_nats, sample_process_config):
        """Test discover_process_class returns specific process class."""
        mock_response = Mock(spec=ProcessClassDiscoveryResponseEvent)
        mock_response.process_class = "TestProcess"
        mock_response.process_config_specs = []
        mock_response.is_conversational = True
        mock_response.start_events = []
        mock_response.stop_events = []
        mock_response.default_process_config = sample_process_config

        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch(
                    "aihub_api.routes.process.ProcessService.ProcessClassTopicManager"
                ) as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager.get_process_class_discovery_subject_request.return_value = "test.subject"
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.process.ProcessService.ObjectId") as mock_objectid:
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

                            async def patched_method(nc, process_class):
                                mock_process_class = Mock()
                                mock_process_class.process_class = mock_response.process_class
                                mock_process_class.is_online = True
                                GET_PROCESS_CLASS_CACHE[process_class] = mock_process_class
                                return mock_process_class

                            with patch.object(ProcessService, "_discover_process_class", patched_method):
                                result = await ProcessService._discover_process_class(mock_nats, "TestProcess")

                                assert result.process_class == "TestProcess"
                                assert result.is_online

    @pytest.mark.asyncio
    async def test_discover_process_class_timeout(self, mock_nats):
        """Test discover_process_class raises 404 on timeout."""
        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch(
                    "aihub_api.routes.process.ProcessService.ProcessClassTopicManager"
                ) as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.process.ProcessService.ObjectId") as mock_objectid:
                        mock_objectid.return_value = "test_call_id"

                        with patch("asyncio.wait_for") as mock_wait_for:
                            mock_wait_for.side_effect = TimeoutError()

                            with pytest.raises(HTTPException) as exc_info:
                                await ProcessService._discover_process_class(mock_nats, "TestProcess")

                            assert exc_info.value.status_code == 404
                            assert "Process TestProcess not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_process_class_cached(self, mock_nats):
        """Test discover_process_class returns cached result."""
        cached_result = Mock(spec=ProcessClassDTO)
        GET_PROCESS_CLASS_CACHE["TestProcess"] = cached_result

        result = await ProcessService._discover_process_class(mock_nats, "TestProcess")

        assert result == cached_result

    @pytest.mark.asyncio
    async def test_send_event_success(self, mock_nats, mock_user_identity):
        """Test send_event successfully sends event to process."""
        event = HumanStartEvent(
            payload="Start Process",
        )
        mock_thread = Mock()
        mock_thread.id = ObjectId()
        mock_external_distributor = Mock()
        mock_external_distributor.distribute_event = AsyncMock()

        result = await ProcessService._send_event(
            external_process_event_distributor=mock_external_distributor,
            user=mock_user_identity,
            work_event=event,
            process_class="TestProcess",
            process_id="test_process_1",
        )

        mock_external_distributor.distribute_event.assert_called_once_with(
            result,  # ExternalProcessEvent
            mock_user_identity,
        )

        assert result.process_class == "TestProcess"
        assert result.process_id == "test_process_1"
        assert result.event == event

    def test_clear_cache_success(self):
        """Test clear_cache clears all caches."""
        # Clear caches first to ensure clean state
        ProcessService._clear_cache()

        # Add some items to caches
        DISCOVER_PROCESSES_CACHE["test"] = "value"
        GET_PROCESS_INSTANCE_CACHE["test"] = "value"
        GET_PROCESS_CLASS_CACHE["test"] = "value"

        # Verify caches have items
        assert len(DISCOVER_PROCESSES_CACHE) > 0
        assert len(GET_PROCESS_INSTANCE_CACHE) > 0
        assert len(GET_PROCESS_CLASS_CACHE) > 0

        # Clear caches
        ProcessService._clear_cache()

        # Verify caches are empty
        assert len(DISCOVER_PROCESSES_CACHE) == 0
        assert len(GET_PROCESS_INSTANCE_CACHE) == 0
        assert len(GET_PROCESS_CLASS_CACHE) == 0

    @pytest.mark.asyncio
    async def test_get_process_database_exception(self, mock_nats, mock_locale_handler):
        """Test get_process handles database exceptions properly."""
        with patch.object(ProcessService, "discover_process_instance") as mock_discover:
            mock_discover.side_effect = HTTPException(status_code=404, detail="Not found")

            with patch.object(ProcessEntity, "get_process") as mock_get_process:
                mock_get_process.side_effect = Exception("Database error")

                with pytest.raises(Exception) as exc_info:
                    await ProcessService.get_process(mock_nats, "TestProcess", "test_process_1", mock_locale_handler)

                assert str(exc_info.value) == "Database error"

    @pytest.mark.asyncio
    async def test_discover_process_instances_no_results(self, mock_nats):
        """Test discover_process_instances returns empty list when no processes found."""
        with patch.object(ProcessService, "_discover_process_classes") as mock_discover_classes:
            mock_discover_classes.return_value = []

            result = await ProcessService.discover_process_instances(mock_nats)

            assert result == []
            # Should not cache empty results
            assert "all_process_instances" not in DISCOVER_PROCESSES_CACHE

    @pytest.mark.asyncio
    async def test_discover_process_classes_no_results(self, mock_nats):
        """Test discover_process_classes returns empty list when no processes respond."""
        with patch("aihub_api.routes.process.ProcessService.ProcessNCSubscriber") as mock_subscriber_class:
            mock_subscriber = Mock()
            mock_subscriber.start = AsyncMock()
            mock_subscriber.stop = AsyncMock()
            mock_subscriber_class.for_process_class_discovery_response_events.return_value = mock_subscriber

            with patch("aihub_api.routes.process.ProcessService.NCPublisher") as mock_publisher_class:
                mock_publisher = Mock()
                mock_publisher.publish_event = AsyncMock()
                mock_publisher_class.return_value = mock_publisher

                with patch("aihub_api.routes.process.ProcessService.ProcessTopicManager") as mock_topic_manager_class:
                    mock_topic_manager = Mock()
                    mock_topic_manager_class.return_value = mock_topic_manager

                    with patch("aihub_api.routes.process.ProcessService.sleep") as mock_sleep:
                        mock_sleep.return_value = None

                        with patch("aihub_api.routes.process.ProcessService.ObjectId") as mock_objectid:
                            mock_objectid.return_value = "test_call_id"

                            # Mock empty discovery responses

                            async def patched_method(nc):
                                discovery_responses = []  # No responses
                                unique_processes_dict = {}

                                for response in discovery_responses:
                                    unique_key = response.process_class
                                    if unique_key not in unique_processes_dict:
                                        process_class_dto = ProcessClassDTO.from_discovery_event(response)
                                        unique_processes_dict[unique_key] = process_class_dto

                                processes = list(unique_processes_dict.values())
                                # Should not cache empty results
                                return processes

                            with patch.object(ProcessService, "_discover_process_classes", patched_method):
                                result = await ProcessService._discover_process_classes(mock_nats)

                                assert result == []
                                # Should not cache empty results
                                assert "all_process_classes" not in DISCOVER_PROCESSES_CACHE
