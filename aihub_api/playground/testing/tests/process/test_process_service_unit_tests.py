from unittest.mock import AsyncMock, Mock, patch

import pytest
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.persistence.process.ProcessClassEntity import ProcessClassEntity
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from fastapi import HTTPException

from aihub_api.routes.process.dto.FullProcessInstanceDTO import FullProcessInstanceDTO
from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.ProcessService import ProcessService
from aihub_api.runners.simulation.process.events.HumanStartWork import HumanStartEvent

enable_logging()


@pytest.fixture
def sample_process_config():
    """Create a sample ProcessConfig for testing."""
    return ProcessConfig(
        process_id="test_process_1",
        name=LocaleString(en="Test Process 1"),
        description=LocaleString(en="A test process for validation"),
        icon="test-icon",
    )


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


class TestProcessServiceUnit:
    """Unit tests for ProcessService DB-first methods."""

    @pytest.mark.asyncio
    async def test_get_process_classes_returns_all(self, mock_locale_handler):
        """Test get_process_classes returns all process classes from DB."""
        mock_entity = Mock(spec=ProcessClassEntity)
        mock_entity.is_online = True

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [mock_entity]

            with patch.object(ProcessClassDTO, "from_entity") as mock_from_entity:
                expected_dto = Mock(spec=ProcessClassDTO)
                mock_from_entity.return_value = expected_dto

                result = await ProcessService.get_process_classes(mock_locale_handler)

                mock_get_all.assert_called_once()
                mock_from_entity.assert_called_once_with(mock_entity, mock_locale_handler)
                assert result == [expected_dto]

    @pytest.mark.asyncio
    async def test_get_process_classes_filters_online(self, mock_locale_handler):
        """Test get_process_classes filters by online status."""
        mock_online = Mock(spec=ProcessClassEntity)
        mock_online.is_online = True
        mock_offline = Mock(spec=ProcessClassEntity)
        mock_offline.is_online = False

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [mock_online, mock_offline]

            with patch.object(ProcessClassDTO, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = Mock(spec=ProcessClassDTO)

                result = await ProcessService.get_process_classes(mock_locale_handler, online=True)

                assert len(result) == 1
                mock_from_entity.assert_called_once_with(mock_online, mock_locale_handler)

    @pytest.mark.asyncio
    async def test_get_process_class_not_found(self, mock_locale_handler):
        """Test get_process_class raises 404 when not found."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get:
            mock_get.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await ProcessService.get_process_class("NonexistentProcess", mock_locale_handler)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_process_instance_success(self, mock_locale_handler):
        """Test get_process_instance returns instance from DB."""
        mock_class_entity = Mock(spec=ProcessClassEntity)
        mock_config_entity = Mock(spec=ProcessConfigEntityDocument)

        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
                mock_find.return_value = mock_config_entity

                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    expected_dto = Mock(spec=FullProcessInstanceDTO)
                    mock_from.return_value = expected_dto

                    result = await ProcessService.get_process_instance("TestProcess", "test_1", mock_locale_handler)

                    assert result == expected_dto
                    mock_get_class.assert_called_once_with("TestProcess")
                    mock_find.assert_called_once_with("TestProcess", "test_1")

    @pytest.mark.asyncio
    async def test_get_process_instance_not_found(self, mock_locale_handler):
        """Test get_process_instance raises 404 when instance not found."""
        mock_class_entity = Mock(spec=ProcessClassEntity)

        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
                mock_find.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.get_process_instance("TestProcess", "nonexistent", mock_locale_handler)

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_process_instance_success(self):
        """Test delete_process_instance removes config from DB."""
        mock_config = Mock(spec=ProcessConfigEntityDocument)

        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_config

            with patch.object(ProcessConfigEntityDocument, "delete_if_exists_for_class_and_id") as mock_delete:
                await ProcessService.delete_process_instance("TestProcess", "test_1")

                mock_delete.assert_called_once_with("TestProcess", "test_1")

    @pytest.mark.asyncio
    async def test_delete_process_instance_not_found(self):
        """Test delete_process_instance raises 404 when not found."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await ProcessService.delete_process_instance("TestProcess", "nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_send_event_success(self, mock_user_identity):
        """Test send_event successfully sends event to process."""
        event = HumanStartEvent(
            payload="Start Process",
        )
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
