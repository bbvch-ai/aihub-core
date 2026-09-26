from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.form import ConfigSpecs, Repeater, VectorStoreInput
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.persistence.process import ProcessClassEntity
from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument
from swiss_ai_hub.core.processes import ProcessConfig

from swiss_ai_hub.api.routes.process.dto.create_process_instance_request import CreateProcessInstanceRequest
from swiss_ai_hub.api.routes.process.dto.full_process_instance_dto import FullProcessInstanceDTO
from swiss_ai_hub.api.routes.process.dto.process_class_dto import ProcessClassDTO
from swiss_ai_hub.api.routes.process.process_service import ProcessService
from swiss_ai_hub.api.runners.simulation.process.events.human_start_work import HumanStartEvent
from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

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
    async def test_get_all_process_instances_skips_record_that_fails_to_build(self, mock_locale_handler):
        """A single instance whose DTO cannot be built must be skipped, not abort the whole sweep."""
        mock_class_entity = Mock(spec=ProcessClassEntity)
        mock_class_entity.is_online = True
        mock_class_entity.process_class = "TestProcess"
        good_config = Mock(spec=ProcessConfigEntityDocument)
        good_config.process_id = "good"
        bad_config = Mock(spec=ProcessConfigEntityDocument)
        bad_config.process_id = "bad"

        with patch.object(ProcessClassEntity, "get_all", return_value=[mock_class_entity]):
            with patch.object(ProcessConfigEntityDocument, "find_for_class", return_value=[good_config, bad_config]):
                with patch.object(FullProcessInstanceDTO, "from_class_and_config") as mock_from:
                    good_dto = Mock(spec=FullProcessInstanceDTO)
                    mock_from.side_effect = [good_dto, ValueError("could not build DTO")]

                    result = await ProcessService.get_all_process_instances(mock_locale_handler)

        assert result == [good_dto]

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


_PROCESS_MODULE = "swiss_ai_hub.api.routes.process.process_service"
_EMPTY_SCOPE_CONFIG = {
    "retrievers": [{"vector_store": {"collection_name": "handbook", "index_namespaces": [], "all_namespaces": False}}]
}


class TestProcessSaveRejectsEmptyNamespaceScope:
    """#1836: no process blueprint embeds a retriever today, but the process save path must not become the bypass."""

    @staticmethod
    def _mock_save_dependencies(stack: ExitStack) -> tuple[Mock, AsyncMock]:
        class_entity = Mock()
        class_entity.is_online = True
        class_entity.process_config_specs.to_specs.return_value = ConfigSpecs(config_class="ReviewProcess")
        class_entity.form_elements = [
            Repeater(name="retrievers", children=[VectorStoreInput(label="Vector store", name="vector_store")])
        ]
        stack.enter_context(
            patch(f"{_PROCESS_MODULE}.ProcessClassEntity.get_by_process_class", return_value=class_entity)
        )
        stack.enter_context(patch(f"{_PROCESS_MODULE}.ModelCreationService"))
        stack.enter_context(patch.object(InstanceConfigHelper, "validate_config_for_create"))
        stack.enter_context(patch.object(InstanceConfigHelper, "validate_config_for_update"))
        config_auth = stack.enter_context(patch(f"{_PROCESS_MODULE}.ConfigAuthorizationService"))
        config_auth.validate_for_user_or_raise = AsyncMock()
        config_doc = stack.enter_context(patch(f"{_PROCESS_MODULE}.ProcessConfigEntityDocument"))
        config_doc.find_for_class_and_id.return_value = None
        return config_doc, config_auth.validate_for_user_or_raise

    @staticmethod
    def _assert_rejected(raised: pytest.ExceptionInfo[HTTPException]) -> None:
        assert raised.value.status_code == 400
        assert raised.value.detail == (
            "Configuration validation failed: retrievers.0.vector_store: "
            "Select at least one namespace to search, or enable all_namespaces."
        )

    @pytest.mark.asyncio
    async def test_create_is_rejected(self):
        request = CreateProcessInstanceRequest(process_id="review", configuration=_EMPTY_SCOPE_CONFIG)

        with ExitStack() as stack:
            config_doc, authorize = self._mock_save_dependencies(stack)
            with pytest.raises(HTTPException) as raised:
                await ProcessService.create_process_instance(
                    "ReviewProcess", request, LocaleHandler(locale="en"), user=Mock()
                )

        self._assert_rejected(raised)
        authorize.assert_not_awaited()
        config_doc.return_value.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_is_rejected(self):
        with ExitStack() as stack:
            config_doc, authorize = self._mock_save_dependencies(stack)
            stored = Mock()
            config_doc.find_for_class_and_id.return_value = stored
            with pytest.raises(HTTPException) as raised:
                await ProcessService.update_process_instance(
                    "ReviewProcess", "review", dict(_EMPTY_SCOPE_CONFIG), LocaleHandler(locale="en"), user=Mock()
                )

        self._assert_rejected(raised)
        authorize.assert_not_awaited()
        stored.save.assert_not_called()
