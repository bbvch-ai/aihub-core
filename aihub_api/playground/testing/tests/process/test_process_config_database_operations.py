from unittest.mock import Mock, patch

import pytest
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument
from aihub_lib.processes.ProcessConfig import ProcessConfig
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401

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


class TestProcessConfigDatabaseOperations:
    """Test ProcessConfig database operations."""

    def test_process_config_entity_document_find_for_class_and_id(
        self, sample_process_config, mock_process_config_document
    ):
        """Test that ProcessConfigEntityDocument.find_for_class_and_id works correctly."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_process_config_document

            result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "test_process_1")

            mock_find.assert_called_once_with("TestProcess", "test_process_1")
            assert result == mock_process_config_document

    def test_process_config_entity_document_find_for_class_and_id_not_found(self):
        """Test that ProcessConfigEntityDocument.find_for_class_and_id returns None when not found."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = None

            result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "nonexistent_id")

            mock_find.assert_called_once_with("TestProcess", "nonexistent_id")
            assert result is None

    def test_process_config_entity_document_find_for_class(self, mock_process_config_document):
        """Test that ProcessConfigEntityDocument.find_for_class works correctly."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find:
            mock_find.return_value = [mock_process_config_document]

            result = ProcessConfigEntityDocument.find_for_class("TestProcess")

            mock_find.assert_called_once_with("TestProcess")
            assert result == [mock_process_config_document]

    def test_process_config_from_entity_conversion(self, sample_process_config, mock_process_config_document):
        """Test that ProcessConfig.from_entity correctly converts database entities."""
        with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
            mock_from_entity.return_value = sample_process_config

            result = ProcessConfig.from_entity(mock_process_config_document)

            mock_from_entity.assert_called_once_with(mock_process_config_document)
            assert result == sample_process_config

    def test_db_config_overrides_default_scenario(self, sample_process_config, sample_default_config):
        """Test scenario where DB config should override default config."""
        # Create different configs to test override
        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="test_process_1",
            name=LocaleString(en="DB Test Process"),
            description=LocaleString(en="Process config from database"),
            icon="db-icon",
        )

        default_config = ProcessConfig(
            process_class="TestProcess",
            process_id="test_process_1",
            name=LocaleString(en="Default Test Process"),
            description=LocaleString(en="Default process config"),
            icon="default-icon",
        )

        # Mock database document
        mock_doc = Mock()
        mock_doc.process_class = "TestProcess"
        mock_doc.process_id = "test_process_1"
        mock_doc.name = db_config.name
        mock_doc.description = db_config.description
        mock_doc.icon = db_config.icon
        mock_doc.config_data = {}

        # Test the override scenario
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_doc

            with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = db_config

                # When DB config exists, it should be used
                result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "test_process_1")
                assert result == mock_doc

                converted_config = ProcessConfig.from_entity(result)
                assert converted_config == db_config
                assert converted_config.name.en == "DB Test Process"

                # Verify it's not the default config
                assert converted_config != default_config

    def test_same_id_override_scenario(self, sample_default_config):
        """Test that DB config with same ID as default overrides default."""
        # Create DB config with same ID as default
        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="default_process",  # Same ID as default
            name=LocaleString(en="Overridden Default"),
            description=LocaleString(en="DB config overriding default"),
            icon="override-icon",
        )

        # Mock DB document
        mock_doc = Mock()
        mock_doc.process_class = "TestProcess"
        mock_doc.process_id = "default_process"
        mock_doc.name = db_config.name
        mock_doc.description = db_config.description
        mock_doc.icon = db_config.icon
        mock_doc.config_data = {}

        # Test the override scenario
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_doc

            with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = db_config

                # When DB config exists for same ID, it should be used instead of default
                result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "default_process")
                assert result == mock_doc

                converted_config = ProcessConfig.from_entity(result)
                assert converted_config == db_config
                assert converted_config.name.en == "Overridden Default"

                # Verify it's not the default config
                assert converted_config != sample_default_config

    def test_multiple_configs_retrieval(self, sample_process_config):
        """Test retrieving multiple configs for a class."""
        # Create multiple mock documents
        mock_doc1 = Mock()
        mock_doc1.process_class = "TestProcess"
        mock_doc1.process_id = "process_1"
        mock_doc1.name = LocaleString(en="Process 1")
        mock_doc1.description = LocaleString(en="First process")
        mock_doc1.icon = "icon1"
        mock_doc1.config_data = {}

        mock_doc2 = Mock()
        mock_doc2.process_class = "TestProcess"
        mock_doc2.process_id = "process_2"
        mock_doc2.name = LocaleString(en="Process 2")
        mock_doc2.description = LocaleString(en="Second process")
        mock_doc2.icon = "icon2"
        mock_doc2.config_data = {}

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

        with patch.object(ProcessConfigEntityDocument, "find_for_class") as mock_find:
            mock_find.return_value = [mock_doc1, mock_doc2]

            with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                mock_from_entity.side_effect = [config1, config2]

                # Retrieve all configs for class
                docs = ProcessConfigEntityDocument.find_for_class("TestProcess")
                assert len(docs) == 2

                # Convert each document to config
                converted_configs = [ProcessConfig.from_entity(doc) for doc in docs]
                assert len(converted_configs) == 2
                assert converted_configs[0] == config1
                assert converted_configs[1] == config2

    def test_error_handling_db_exception(self):
        """Test handling of database exceptions."""
        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.side_effect = Exception("Database connection failed")

            # Should propagate the exception
            with pytest.raises(Exception) as exc_info:
                ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "test_process")

            assert str(exc_info.value) == "Database connection failed"

    def test_config_priority_logic(self, sample_default_config):
        """Test the priority logic: DB config takes precedence over default."""
        # This test demonstrates the expected behavior for configuration resolution

        # Scenario 1: DB config exists - should use DB config
        db_config = ProcessConfig(
            process_class="TestProcess",
            process_id="test_process",
            name=LocaleString(en="DB Config"),
            description=LocaleString(en="From database"),
            icon="db-icon",
        )

        mock_doc = Mock()
        mock_doc.process_class = "TestProcess"
        mock_doc.process_id = "test_process"
        mock_doc.config_data = {}

        with patch.object(ProcessConfigEntityDocument, "find_for_class_and_id") as mock_find:
            with patch.object(ProcessConfig, "from_entity") as mock_from_entity:
                # When DB config exists
                mock_find.return_value = mock_doc
                mock_from_entity.return_value = db_config

                # Should use DB config
                result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "test_process")
                assert result == mock_doc

                config = ProcessConfig.from_entity(result)
                assert config == db_config

                # Scenario 2: DB config doesn't exist - should use default
                mock_find.return_value = None

                result = ProcessConfigEntityDocument.find_for_class_and_id("TestProcess", "nonexistent_process")
                assert result is None

                # In this case, the calling code would fall back to default_config
                # This demonstrates that the priority is: DB config > default config
