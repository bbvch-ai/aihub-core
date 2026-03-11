from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.persistence.process import ProcessClassEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument
from swiss_ai_hub.core.testing import mock_role_entity_methods

from swiss_ai_hub.api.routes.process.dto.full_process_instance_dto import FullProcessInstanceDTO
from swiss_ai_hub.api.routes.process.dto.process_class_dto import ProcessClassDTO
from swiss_ai_hub.api.routes.process.process_service import ProcessService

enable_logging()


@pytest.fixture
def mock_locale_handler():
    """Create a mock LocaleHandler."""
    return Mock(spec=LocaleHandler)


@pytest.fixture
def mock_class_entity():
    """Create a mock ProcessClassEntity."""
    entity = Mock(spec=ProcessClassEntity)
    entity.process_class = "TestProcess"
    entity.is_online = True
    entity.icon = "test-icon"
    return entity


@pytest.fixture
def mock_config_entity():
    """Create a mock ProcessConfigEntityDocument."""
    entity = Mock(spec=ProcessConfigEntityDocument)
    entity.process_class = "TestProcess"
    entity.process_id = "test_process_1"
    entity.name = Mock()
    entity.name.to_locale_string.return_value = LocaleString(en="Test Process 1")
    entity.description = Mock()
    entity.description.to_locale_string.return_value = LocaleString(en="A test process")
    entity.icon = "test-icon"
    entity.config_data = {}
    return entity


@pytest.fixture
def mock_config_entity_2():
    """Create a second mock ProcessConfigEntityDocument."""
    entity = Mock(spec=ProcessConfigEntityDocument)
    entity.process_class = "TestProcess"
    entity.process_id = "test_process_2"
    entity.name = Mock()
    entity.name.to_locale_string.return_value = LocaleString(en="Test Process 2")
    entity.description = Mock()
    entity.description.to_locale_string.return_value = LocaleString(en="Second test process")
    entity.icon = "db-icon2"
    entity.config_data = {"key": "value"}
    return entity


class TestProcessServiceDatabaseIntegration:
    """Test ProcessService database integration with DB-first CRUD methods."""

    @pytest.mark.asyncio
    async def test_get_process_class_instances_returns_all(
        self, mock_locale_handler, mock_class_entity, mock_config_entity, mock_config_entity_2
    ):
        """Test that get_process_class_instances returns all instances for a class from DB."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_config_entity, mock_config_entity_2]

                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    dto1 = Mock(spec=FullProcessInstanceDTO)
                    dto2 = Mock(spec=FullProcessInstanceDTO)
                    mock_from.side_effect = [dto1, dto2]

                    result = await ProcessService.get_process_class_instances("TestProcess", mock_locale_handler)

                    mock_get_class.assert_called_once_with("TestProcess")
                    mock_find_configs.assert_called_once_with("TestProcess")
                    assert len(result) == 2
                    assert result == [dto1, dto2]

    @pytest.mark.asyncio
    async def test_get_process_class_instances_empty(self, mock_locale_handler, mock_class_entity):
        """Test that get_process_class_instances returns empty list when no instances exist."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []

                result = await ProcessService.get_process_class_instances("TestProcess", mock_locale_handler)

                assert result == []

    @pytest.mark.asyncio
    async def test_get_process_class_instances_class_not_found(self, mock_locale_handler):
        """Test that get_process_class_instances raises 404 when class not found."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await ProcessService.get_process_class_instances("NonexistentProcess", mock_locale_handler)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_process_instance_returns_dto(self, mock_locale_handler, mock_class_entity, mock_config_entity):
        """Test that get_process_instance returns a FullProcessInstanceDTO from DB."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
                mock_find.return_value = mock_config_entity

                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    expected_dto = Mock(spec=FullProcessInstanceDTO)
                    mock_from.return_value = expected_dto

                    result = await ProcessService.get_process_instance(
                        "TestProcess", "test_process_1", mock_locale_handler
                    )

                    mock_get_class.assert_called_once_with("TestProcess")
                    mock_find.assert_called_once_with("TestProcess", "test_process_1")
                    mock_from.assert_called_once_with(mock_class_entity, mock_config_entity, mock_locale_handler)
                    assert result == expected_dto

    @pytest.mark.asyncio
    async def test_get_process_instance_not_found(self, mock_locale_handler, mock_class_entity):
        """Test that get_process_instance raises 404 when instance not found in DB."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = mock_class_entity

            with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
                mock_find.return_value = None

                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.get_process_instance("TestProcess", "nonexistent_process", mock_locale_handler)

                assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_process_instance_class_not_found(self, mock_locale_handler):
        """Test that get_process_instance raises 404 when class not found."""
        with patch.object(ProcessClassEntity, "get_by_process_class") as mock_get_class:
            mock_get_class.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await ProcessService.get_process_instance("NonexistentProcess", "test_1", mock_locale_handler)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_all_process_instances_cross_class(
        self, mock_locale_handler, mock_config_entity, mock_config_entity_2
    ):
        """Test that get_all_process_instances returns instances from all classes."""
        class_entity_1 = Mock(spec=ProcessClassEntity)
        class_entity_1.process_class = "ProcessA"
        class_entity_1.is_online = True

        class_entity_2 = Mock(spec=ProcessClassEntity)
        class_entity_2.process_class = "ProcessB"
        class_entity_2.is_online = True

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [class_entity_1, class_entity_2]

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find:
                mock_find.side_effect = [[mock_config_entity], [mock_config_entity_2]]

                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    dto1 = Mock(spec=FullProcessInstanceDTO)
                    dto2 = Mock(spec=FullProcessInstanceDTO)
                    mock_from.side_effect = [dto1, dto2]

                    result = await ProcessService.get_all_process_instances(mock_locale_handler)

                    assert len(result) == 2
                    assert result == [dto1, dto2]

    @pytest.mark.asyncio
    async def test_get_all_process_instances_filters_online(self, mock_locale_handler, mock_config_entity):
        """Test that get_all_process_instances filters by online status."""
        online_class = Mock(spec=ProcessClassEntity)
        online_class.process_class = "OnlineProcess"
        online_class.is_online = True

        offline_class = Mock(spec=ProcessClassEntity)
        offline_class.process_class = "OfflineProcess"
        offline_class.is_online = False

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [online_class, offline_class]

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find:
                mock_find.return_value = [mock_config_entity]

                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    dto = Mock(spec=FullProcessInstanceDTO)
                    mock_from.return_value = dto

                    result = await ProcessService.get_all_process_instances(mock_locale_handler, online=True)

                    assert len(result) == 1
                    # find_for_class should only be called for the online class
                    mock_find.assert_called_once_with("OnlineProcess")

    @pytest.mark.asyncio
    async def test_get_all_process_instances_empty(self, mock_locale_handler):
        """Test that get_all_process_instances returns empty list when no classes exist."""
        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = []

            result = await ProcessService.get_all_process_instances(mock_locale_handler)

            assert result == []

    @pytest.mark.asyncio
    async def test_delete_process_instance_success(self):
        """Test that delete_process_instance removes config from DB."""
        mock_config = Mock(spec=ProcessConfigEntityDocument)

        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_config

            with patch.object(ProcessConfigEntityDocument, "delete_if_exists_for_class_and_id") as mock_delete:
                await ProcessService.delete_process_instance("TestProcess", "test_1")

                mock_find.assert_called_once_with("TestProcess", "test_1")
                mock_delete.assert_called_once_with("TestProcess", "test_1")

    @pytest.mark.asyncio
    async def test_delete_process_instance_not_found(self):
        """Test that delete_process_instance raises 404 when not found."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                await ProcessService.delete_process_instance("TestProcess", "nonexistent")

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_process_configuration_returns_config_data(self):
        """Test that get_process_configuration returns config data from DB."""
        mock_config = Mock(spec=ProcessConfigEntityDocument)
        mock_config.config_data = {"key": "value", "nested": {"a": 1}}

        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_config

            result = await ProcessService.get_process_configuration("TestProcess", "test_1")

            assert result == {"key": "value", "nested": {"a": 1}}

    @pytest.mark.asyncio
    async def test_get_process_configuration_returns_empty_when_no_config(self):
        """Test that get_process_configuration returns empty dict when no config exists."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = None

            result = await ProcessService.get_process_configuration("TestProcess", "test_1")

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_process_configuration_returns_empty_when_config_data_is_none(self):
        """Test that get_process_configuration returns empty dict when config_data is None."""
        mock_config = Mock(spec=ProcessConfigEntityDocument)
        mock_config.config_data = None

        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_config

            result = await ProcessService.get_process_configuration("TestProcess", "test_1")

            assert result == {}

    @pytest.mark.asyncio
    async def test_get_process_classes_returns_all(self, mock_locale_handler):
        """Test that get_process_classes returns all classes from DB."""
        entity1 = Mock(spec=ProcessClassEntity)
        entity1.is_online = True
        entity2 = Mock(spec=ProcessClassEntity)
        entity2.is_online = False

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [entity1, entity2]

            with patch.object(ProcessClassDTO, "from_entity") as mock_from:
                dto1 = Mock(spec=ProcessClassDTO)
                dto2 = Mock(spec=ProcessClassDTO)
                mock_from.side_effect = [dto1, dto2]

                result = await ProcessService.get_process_classes(mock_locale_handler)

                assert len(result) == 2
                assert result == [dto1, dto2]

    @pytest.mark.asyncio
    async def test_get_process_classes_filters_online(self, mock_locale_handler):
        """Test that get_process_classes filters by online status."""
        online = Mock(spec=ProcessClassEntity)
        online.is_online = True
        offline = Mock(spec=ProcessClassEntity)
        offline.is_online = False

        with patch.object(ProcessClassEntity, "get_all") as mock_get_all:
            mock_get_all.return_value = [online, offline]

            with patch.object(ProcessClassDTO, "from_entity") as mock_from:
                dto = Mock(spec=ProcessClassDTO)
                mock_from.return_value = dto

                result = await ProcessService.get_process_classes(mock_locale_handler, online=True)

                assert len(result) == 1
                mock_from.assert_called_once_with(online, mock_locale_handler)
