from unittest.mock import Mock, patch

import pytest
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.logging.logger import enable_logging
from fastapi import HTTPException

from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.ProcessService import GET_PROCESS_INSTANCE_CACHE, ProcessService

enable_logging()


@pytest.fixture(autouse=True)
def cleanup_db_and_cache(sample_process_config):
    ProcessService.clear_cache()
    yield
    ProcessService.clear_cache()


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
def sample_default_config():
    """Create a sample default ProcessConfig for testing."""
    return ProcessConfig(
        process_class="TestProcess",
        process_id="default_process",
        name=LocaleString(en="Default Test Process"),
        description=LocaleString(en="Default test process configuration"),
        icon="default-icon",
    )


@pytest.fixture
def sample_process_class(sample_default_config):
    """Create a sample ProcessClass with default config."""
    mock_process_class = Mock(spec=ProcessClassDTO)
    mock_process_class.process_class = "TestProcess"
    mock_process_class.default_process_config = sample_default_config
    return mock_process_class


@pytest.fixture
def mock_process_config_document():
    """Create a mock ProcessConfigEntityDocument."""
    mock_doc = Mock()
    mock_doc.process_class = "TestProcess"
    mock_doc.process_id = "test_process_1"
    mock_doc.name = LocaleString(en="Test Process 1")
    mock_doc.description = LocaleString(en="A test process")
    mock_doc.icon = "test-icon"
    mock_doc.config_data = {}
    return mock_doc


class TestProcessServiceDatabaseIntegration:
    """Test ProcessService database integration functionality."""

    @pytest.mark.asyncio
    async def test_discover_process_instance_uses_db_config_when_available(
        self, sample_process_config, sample_process_class, mock_process_config_document
    ):
        """Test that discover_process_instance uses DB config when available, matching AgentService behavior."""
        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = sample_process_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                        mock_instance = Mock()
                        mock_create_instance.return_value = mock_instance

                        result = await ProcessService.discover_process_instance(Mock(), "TestProcess", "test_process_1")

                        # Verify it used DB config
                        mock_find_configs.assert_called_once_with("TestProcess")
                        mock_from_entity.assert_called_once_with(mock_process_config_document)
                        mock_create_instance.assert_called_once_with(
                            class_dto=sample_process_class, process_config=sample_process_config
                        )
                        assert result == mock_instance

    @pytest.mark.asyncio
    async def test_discover_process_instance_falls_back_to_default_when_no_db_config(
        self, sample_default_config, sample_process_class
    ):
        """Test that discover_process_instance falls back to default config when no DB config exists."""
        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs

                with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                    mock_instance = Mock()
                    mock_create_instance.return_value = mock_instance

                    result = await ProcessService.discover_process_instance(Mock(), "TestProcess", "default_process")

                    # Verify it used default config from class
                    mock_create_instance.assert_called_once_with(
                        class_dto=sample_process_class, process_config=sample_default_config
                    )
                    assert result == mock_instance

    @pytest.mark.asyncio
    async def test_discover_process_instance_raises_404_when_process_not_found(self, sample_process_class):
        """Test that discover_process_instance raises 404 when process ID not found."""
        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs

                # Process ID doesn't match default config
                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.discover_process_instance(Mock(), "TestProcess", "nonexistent_process")

                assert exc_info.value.status_code == 404
                assert "Process TestProcess.nonexistent_process not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_process_instances_includes_db_and_default_configs(
        self, sample_process_config, sample_default_config, sample_process_class, mock_process_config_document
    ):
        """Test that discover_process_instances includes both DB configs and default config."""
        with patch.object(ProcessService, "discover_process_classes") as mock_discover_classes:
            mock_discover_classes.return_value = [sample_process_class]

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = sample_process_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                        mock_db_instance = Mock()
                        mock_db_instance.process_id = "test_process_1"
                        mock_default_instance = Mock()
                        mock_default_instance.process_id = "default_process"

                        mock_create_instance.side_effect = [mock_db_instance, mock_default_instance]

                        with patch.object(ProcessInstanceDTO, "create_or_update_process_entity"):
                            result = await ProcessService.discover_process_instances(Mock())

                            # Should create instances from both DB config and default config
                            assert len(result) == 2
                            assert mock_create_instance.call_count == 2

                            # First call: DB config
                            first_call = mock_create_instance.call_args_list[0]
                            assert first_call[1]["class_dto"] == sample_process_class
                            assert first_call[1]["process_config"] == sample_process_config

                            # Second call: Default config (because default ID not in DB)
                            second_call = mock_create_instance.call_args_list[1]
                            assert second_call[1]["class_dto"] == sample_process_class
                            assert second_call[1]["process_config"] == sample_default_config

    @pytest.mark.asyncio
    async def test_discover_process_instances_avoids_duplicate_default_when_in_db(
        self, sample_default_config, sample_process_class
    ):
        """Test that discover_process_instances doesn't duplicate default config if it exists in DB."""
        # Create DB config with same ID as default
        db_config_with_default_id = ProcessConfig(
            process_class="TestProcess",
            process_id="default_process",  # Same as default
            name=LocaleString(en="DB Override Default"),
            description=LocaleString(en="DB config overriding default"),
            icon="override-icon",
        )

        mock_db_document = Mock()
        mock_db_document.process_class = "TestProcess"
        mock_db_document.process_id = "default_process"
        mock_db_document.config_data = {}

        with patch.object(ProcessService, "discover_process_classes") as mock_discover_classes:
            mock_discover_classes.return_value = [sample_process_class]

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_db_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config_with_default_id

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                        mock_instance = Mock()
                        mock_instance.process_id = "default_process"
                        mock_create_instance.return_value = mock_instance

                        with patch.object(ProcessInstanceDTO, "create_or_update_process_entity"):
                            result = await ProcessService.discover_process_instances(Mock())

                            # Should only create one instance (DB config overrides default)
                            assert len(result) == 1
                            assert mock_create_instance.call_count == 1

                            # Verify it used DB config, not default config
                            call_args = mock_create_instance.call_args_list[0]
                            assert call_args[1]["process_config"] == db_config_with_default_id
                            assert call_args[1]["process_config"].name.en == "DB Override Default"

    @pytest.mark.asyncio
    async def test_caching_behavior_for_process_instances(self, sample_default_config, sample_process_class):
        """Test that process instance discovery results are cached properly."""
        process_class = sample_process_class.process_class
        process_id = sample_default_config.process_id
        cache_key = (process_class, process_id)

        # Clear cache first
        ProcessService.clear_cache()

        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []

                with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                    mock_instance = Mock()
                    mock_create_instance.return_value = mock_instance

                    # First call should hit the service
                    result1 = await ProcessService.discover_process_instance(Mock(), process_class, process_id)
                    assert result1 == mock_instance
                    assert mock_create_instance.call_count == 1

                    # Second call should use cache
                    result2 = await ProcessService.discover_process_instance(Mock(), process_class, process_id)
                    assert result2 == mock_instance
                    assert mock_create_instance.call_count == 1  # Should not be called again

                    # Verify cache was used
                    assert cache_key in GET_PROCESS_INSTANCE_CACHE
                    assert GET_PROCESS_INSTANCE_CACHE[cache_key] == mock_instance

    def test_cache_clear_functionality(self):
        """Test that ProcessService.clear_cache() clears all caches."""
        # Populate caches
        GET_PROCESS_INSTANCE_CACHE[("TestProcess", "test_id")] = Mock()

        # Clear caches
        ProcessService.clear_cache()

        # Verify all caches are cleared
        assert len(GET_PROCESS_INSTANCE_CACHE) == 0

    @pytest.mark.asyncio
    async def test_process_config_priority_integration(
        self, sample_process_config, sample_default_config, sample_process_class
    ):
        """Integration test demonstrating DB config takes priority over default config."""
        # This test shows the full priority resolution flow

        # Mock DB document that overrides default
        mock_db_document = Mock()
        mock_db_document.process_class = "TestProcess"
        mock_db_document.process_id = "test_process_1"
        mock_db_document.config_data = {}

        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="test_process_1",
            name=LocaleString(en="DB Config Takes Priority"),
            description=LocaleString(en="This config came from database"),
            icon="db-priority-icon",
        )

        with patch.object(ProcessService, "discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                # Scenario 1: DB config exists
                mock_find_configs.return_value = [mock_db_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_create_instance:
                        mock_instance = Mock()
                        mock_create_instance.return_value = mock_instance

                        await ProcessService.discover_process_instance(Mock(), "TestProcess", "test_process_1")

                        # Verify DB config was used, not default
                        call_args = mock_create_instance.call_args_list[0]
                        used_config = call_args[1]["process_config"]
                        assert used_config == db_config
                        assert used_config.name.en == "DB Config Takes Priority"

                        # Verify it's NOT the default config
                        assert used_config != sample_default_config
