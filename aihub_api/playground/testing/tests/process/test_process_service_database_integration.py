from unittest.mock import Mock, patch

import pytest
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from fastapi import HTTPException

from aihub_api.routes.process.dto.ProcessClassDTO import ProcessClassDTO
from aihub_api.routes.process.dto.ProcessInstanceDTO import ProcessInstanceDTO
from aihub_api.routes.process.ProcessService import GET_PROCESS_INSTANCE_CACHE, ProcessService

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
def mock_process_config_document(sample_process_config):
    """Create a mock ProcessConfigEntityDocument."""
    mock_doc = Mock()
    mock_doc.process_class = sample_process_config.process_class
    mock_doc.process_id = sample_process_config.process_id
    mock_doc.name = sample_process_config.name
    mock_doc.description = sample_process_config.description
    mock_doc.icon = sample_process_config.icon
    mock_doc.config_data = {}
    return mock_doc


@pytest.fixture
def mock_nats():
    """Create a mock NATS connection."""
    return Mock()


class TestProcessServiceDatabaseIntegration:
    """Test ProcessService database integration and config override logic."""

    @pytest.mark.asyncio
    async def test_discover_process_instance_with_db_config(
        self, mock_nats, sample_process_config, sample_process_class, mock_process_config_document
    ):
        """Test that ProcessService.discover_process_instance correctly fetches and uses DB config."""
        # Clear any existing cache
        ProcessService._clear_cache()

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = sample_process_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=ProcessInstanceDTO)
                        mock_instance.process_config = sample_process_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await ProcessService.discover_process_instance(
                            nc=mock_nats, process_class="TestProcess", process_id="test_process_1"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                        mock_find_configs.assert_called_once_with("TestProcess")
                        mock_from_entity.assert_called_once_with(mock_process_config_document)
                        mock_from_class_config.assert_called_once_with(
                            class_dto=sample_process_class, process_config=sample_process_config
                        )

                        # Verify the result
                        assert result == mock_instance
                        assert result.process_config == sample_process_config

    @pytest.mark.asyncio
    async def test_discover_process_instance_fallback_to_default(
        self, mock_nats, sample_default_config, sample_process_class
    ):
        """Test that ProcessService.discover_process_instance falls back to default config when no DB config exists."""
        # Clear any existing cache
        ProcessService._clear_cache()

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                    mock_instance = Mock(spec=ProcessInstanceDTO)
                    mock_instance.process_config = sample_default_config
                    mock_from_class_config.return_value = mock_instance

                    # Execute the method
                    result = await ProcessService.discover_process_instance(
                        nc=mock_nats, process_class="TestProcess", process_id="default_process"
                    )

                    # Verify the flow
                    mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                    mock_find_configs.assert_called_once_with("TestProcess")
                    mock_from_class_config.assert_called_once_with(
                        class_dto=sample_process_class, process_config=sample_default_config
                    )

                    # Verify the result uses default config
                    assert result == mock_instance
                    assert result.process_config == sample_default_config

    @pytest.mark.asyncio
    async def test_discover_process_instance_db_config_overrides_default(
        self, mock_nats, sample_process_class, mock_process_config_document
    ):
        """Test that DB config overrides default config when both have the same process_id."""
        # Clear any existing cache
        ProcessService._clear_cache()

        # Create a DB config with same ID as default
        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="default_process",  # Same ID as default
            name=LocaleString(en="DB Override Config"),
            description=LocaleString(en="DB config overriding default"),
            icon="db-icon",
        )

        # Mock the document to have the same ID as default
        mock_process_config_document.process_id = "default_process"

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=ProcessInstanceDTO)
                        mock_instance.process_config = db_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await ProcessService.discover_process_instance(
                            nc=mock_nats, process_class="TestProcess", process_id="default_process"
                        )

                        # Verify the flow - should use DB config, not default
                        mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                        mock_find_configs.assert_called_once_with("TestProcess")
                        mock_from_entity.assert_called_once_with(mock_process_config_document)
                        mock_from_class_config.assert_called_once_with(
                            class_dto=sample_process_class,
                            process_config=db_config,  # Should use DB config, not default
                        )

                        # Verify the result uses DB config
                        assert result == mock_instance
                        assert result.process_config == db_config
                        assert result.process_config.name.en == "DB Override Config"

    @pytest.mark.asyncio
    async def test_discover_process_instance_not_found(self, mock_nats, sample_process_class):
        """Test that ProcessService.discover_process_instance raises 404 when process not found."""
        # Clear any existing cache
        ProcessService._clear_cache()

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                # Execute the method with non-existent process_id
                with pytest.raises(HTTPException) as exc_info:
                    await ProcessService.discover_process_instance(
                        nc=mock_nats, process_class="TestProcess", process_id="nonexistent_process"
                    )

                # Verify the exception
                assert exc_info.value.status_code == 404
                assert "Process TestProcess.nonexistent_process not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_process_instances_by_class_with_db_and_default(
        self,
        mock_nats,
        sample_process_class,
        mock_process_config_document,
        sample_process_config,
        sample_default_config,
    ):
        """Test that ProcessService.discover_process_instances_by_class includes both DB and default configs."""
        # Clear any existing cache
        ProcessService._clear_cache()

        # Create a second DB config with different ID
        mock_doc2 = Mock()
        mock_doc2.process_class = "TestProcess"
        mock_doc2.process_id = "db_process_2"
        mock_doc2.name = LocaleString(en="DB Process 2")
        mock_doc2.description = LocaleString(en="Second DB process")
        mock_doc2.icon = "db-icon2"
        mock_doc2.config_data = {}

        config2 = ProcessConfig(
            process_class="TestProcess",
            process_id="db_process_2",
            name=LocaleString(en="DB Process 2"),
            description=LocaleString(en="Second DB process"),
            icon="db-icon2",
        )

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document, mock_doc2]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.side_effect = [sample_process_config, config2]

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance1 = Mock(spec=ProcessInstanceDTO)
                        mock_instance1.process_config = sample_process_config
                        mock_instance2 = Mock(spec=ProcessInstanceDTO)
                        mock_instance2.process_config = config2
                        mock_instance3 = Mock(spec=ProcessInstanceDTO)
                        mock_instance3.process_config = sample_default_config

                        mock_from_class_config.side_effect = [mock_instance1, mock_instance2, mock_instance3]

                        # Execute the method
                        result = await ProcessService.discover_process_instances_by_class(
                            nc=mock_nats, process_class="TestProcess"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                        mock_find_configs.assert_called_once_with("TestProcess")
                        assert mock_from_entity.call_count == 2
                        assert mock_from_class_config.call_count == 3  # 2 DB configs + 1 default

                        # Verify the result includes all configs
                        assert len(result) == 3
                        process_ids = [instance.process_config.process_id for instance in result]
                        assert "test_process_1" in process_ids
                        assert "db_process_2" in process_ids
                        assert "default_process" in process_ids

    @pytest.mark.asyncio
    async def test_discover_process_instances_by_class_excludes_default_when_db_has_same_id(
        self, mock_nats, sample_process_class, mock_process_config_document, sample_default_config
    ):
        """Test that default config is excluded when DB has config with same process_id."""
        # Clear any existing cache
        ProcessService._clear_cache()

        # Create DB config with same ID as default
        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="default_process",  # Same ID as default
            name=LocaleString(en="DB Override Config"),
            description=LocaleString(en="DB config overriding default"),
            icon="db-icon",
        )

        mock_process_config_document.process_id = "default_process"

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_process_config_document]

                with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config

                    with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=ProcessInstanceDTO)
                        mock_instance.process_config = db_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await ProcessService.discover_process_instances_by_class(
                            nc=mock_nats, process_class="TestProcess"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                        mock_find_configs.assert_called_once_with("TestProcess")
                        mock_from_entity.assert_called_once_with(mock_process_config_document)
                        mock_from_class_config.assert_called_once()  # Only called once for DB config

                        # Verify the result includes only DB config, not default
                        assert len(result) == 1
                        assert result[0].process_config == db_config
                        assert result[0].process_config.name.en == "DB Override Config"

    @pytest.mark.asyncio
    async def test_discover_process_instances_by_class_cache_behavior(self, mock_nats, sample_process_class):
        """Test that ProcessService.discover_process_instances_by_class uses cache correctly."""
        # Clear any existing cache
        ProcessService._clear_cache()

        cached_result = [Mock(spec=ProcessInstanceDTO)]
        cache_key = ("TestProcess", "*")
        GET_PROCESS_INSTANCE_CACHE[cache_key] = cached_result

        # Execute the method
        result = await ProcessService.discover_process_instances_by_class(nc=mock_nats, process_class="TestProcess")

        # Verify cached result is returned
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_process_instance_cache_behavior(self, mock_nats, sample_process_class):
        """Test that ProcessService.discover_process_instance uses cache correctly."""
        # Clear any existing cache
        ProcessService._clear_cache()

        cached_result = Mock(spec=ProcessInstanceDTO)
        cache_key = ("TestProcess", "test_process_1")
        GET_PROCESS_INSTANCE_CACHE[cache_key] = cached_result

        # Execute the method
        result = await ProcessService.discover_process_instance(
            nc=mock_nats, process_class="TestProcess", process_id="test_process_1"
        )

        # Verify cached result is returned
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_process_instances_by_class_only_default_config(
        self, mock_nats, sample_process_class, sample_default_config
    ):
        """Test that discover_process_instances_by_class returns only default config when no DB configs exist."""
        # Clear any existing cache
        ProcessService._clear_cache()

        with patch.object(ProcessService, "_discover_process_class") as mock_discover_class:
            mock_discover_class.return_value = sample_process_class

            with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                with patch.object(ProcessInstanceDTO, "from_class_and_config") as mock_from_class_config:
                    mock_instance = Mock(spec=ProcessInstanceDTO)
                    mock_instance.process_config = sample_default_config
                    mock_from_class_config.return_value = mock_instance

                    # Execute the method
                    result = await ProcessService.discover_process_instances_by_class(
                        nc=mock_nats, process_class="TestProcess"
                    )

                    # Verify the flow
                    mock_discover_class.assert_called_once_with(mock_nats, "TestProcess")
                    mock_find_configs.assert_called_once_with("TestProcess")
                    mock_from_class_config.assert_called_once_with(
                        class_dto=sample_process_class, process_config=sample_default_config
                    )

                    # Verify the result includes only the default config
                    assert len(result) == 1
                    assert result[0].process_config == sample_default_config
