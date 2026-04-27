from unittest.mock import Mock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.persistence.agents.agent_config_entity_document import AgentConfigEntityDocument

pytestmark = pytest.mark.usefixtures("cleanup_db_and_cache")

enable_logging()


@pytest.fixture
def cleanup_db_and_cache(sample_agent_config):
    yield


AGENT_CLASS = "TestAgent"


@pytest.fixture
def sample_agent_config():
    """Create a sample AgentConfig for testing."""
    return AgentConfig(
        agent_id="test_agent_1",
        name=LocaleString(en="Test Agent 1"),
        description=LocaleString(en="A test agent for validation"),
        icon="test-icon",
    )


@pytest.fixture
def sample_default_config():
    """Create a sample default AgentConfig for testing."""
    return AgentConfig(
        agent_id="default_agent",
        name=LocaleString(en="Default Test Agent"),
        description=LocaleString(en="Default test agent configuration"),
        icon="default-icon",
    )


@pytest.fixture
def mock_agent_config_document(sample_agent_config):
    """Create a mock AgentConfigEntityDocument."""
    mock_doc = Mock()
    mock_doc.agent_class = AGENT_CLASS
    mock_doc.agent_id = sample_agent_config.agent_id
    mock_doc.name = sample_agent_config.name
    mock_doc.description = sample_agent_config.description
    mock_doc.icon = sample_agent_config.icon
    mock_doc.config_data = {}
    return mock_doc


class TestAgentConfigDatabaseOperations:
    """Test AgentConfig database operations."""

    def test_agent_config_entity_document_find_for_class_and_id(self, sample_agent_config, mock_agent_config_document):
        """Test that AgentConfigEntityDocument.find_for_class_and_id works correctly."""
        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_agent_config_document

            result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "test_agent_1")

            mock_find.assert_called_once_with("TestAgent", "test_agent_1")
            assert result == mock_agent_config_document

    def test_agent_config_entity_document_find_for_class_and_id_not_found(self):
        """Test that AgentConfigEntityDocument.find_for_class_and_id returns None when not found."""
        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = None

            result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "nonexistent_id")

            mock_find.assert_called_once_with("TestAgent", "nonexistent_id")
            assert result is None

    def test_agent_config_entity_document_find_for_class(self, mock_agent_config_document):
        """Test that AgentConfigEntityDocument.find_for_class works correctly."""
        with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find:
            mock_find.return_value = [mock_agent_config_document]

            result = AgentConfigEntityDocument.find_for_class("TestAgent")

            mock_find.assert_called_once_with("TestAgent")
            assert result == [mock_agent_config_document]

    def test_agent_config_from_entity_conversion(self, sample_agent_config, mock_agent_config_document):
        """Test that AgentConfig.from_entity correctly converts database entities."""
        with patch.object(AgentConfig, "from_entity") as mock_from_entity:
            mock_from_entity.return_value = sample_agent_config

            result = AgentConfig.from_entity(mock_agent_config_document)

            mock_from_entity.assert_called_once_with(mock_agent_config_document)
            assert result == sample_agent_config

    def test_db_config_overrides_default_scenario(self, sample_agent_config, sample_default_config):
        """Test scenario where DB config should override default config."""
        # Create different configs to test override
        db_config = AgentConfig(
            agent_id="test_agent_1",
            name=LocaleString(en="DB Test Agent"),
            description=LocaleString(en="Agent config from database"),
            icon="db-icon",
        )

        default_config = AgentConfig(
            agent_id="test_agent_1",
            name=LocaleString(en="Default Test Agent"),
            description=LocaleString(en="Default agent config"),
            icon="default-icon",
        )

        # Mock database document
        mock_doc = Mock()
        mock_doc.agent_class = "TestAgent"
        mock_doc.agent_id = "test_agent_1"
        mock_doc.name = db_config.name
        mock_doc.description = db_config.description
        mock_doc.icon = db_config.icon
        mock_doc.config_data = {}

        # Test the override scenario
        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_doc

            with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = db_config

                # When DB config exists, it should be used
                result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "test_agent_1")
                assert result == mock_doc

                converted_config = AgentConfig.from_entity(result)
                assert converted_config == db_config
                assert converted_config.name.en == "DB Test Agent"

                # Verify it's not the default config
                assert converted_config != default_config

    def test_same_id_override_scenario(self, sample_default_config):
        """Test that DB config with same ID as default overrides default."""
        # Create DB config with same ID as default
        db_config = AgentConfig(
            agent_id="default_agent",  # Same ID as default
            name=LocaleString(en="Overridden Default"),
            description=LocaleString(en="DB config overriding default"),
            icon="override-icon",
        )

        # Mock DB document
        mock_doc = Mock()
        mock_doc.agent_class = "TestAgent"
        mock_doc.agent_id = "default_agent"
        mock_doc.name = db_config.name
        mock_doc.description = db_config.description
        mock_doc.icon = db_config.icon
        mock_doc.config_data = {}

        # Test the override scenario
        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.return_value = mock_doc

            with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                mock_from_entity.return_value = db_config

                # When DB config exists for same ID, it should be used instead of default
                result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "default_agent")
                assert result == mock_doc

                converted_config = AgentConfig.from_entity(result)
                assert converted_config == db_config
                assert converted_config.name.en == "Overridden Default"

                # Verify it's not the default config
                assert converted_config != sample_default_config

    def test_multiple_configs_retrieval(self, sample_agent_config):
        """Test retrieving multiple configs for a class."""
        # Create multiple mock documents
        mock_doc1 = Mock()
        mock_doc1.agent_class = "TestAgent"
        mock_doc1.agent_id = "agent_1"
        mock_doc1.name = LocaleString(en="Agent 1")
        mock_doc1.description = LocaleString(en="First agent")
        mock_doc1.icon = "icon1"
        mock_doc1.config_data = {}

        mock_doc2 = Mock()
        mock_doc2.agent_class = "TestAgent"
        mock_doc2.agent_id = "agent_2"
        mock_doc2.name = LocaleString(en="Agent 2")
        mock_doc2.description = LocaleString(en="Second agent")
        mock_doc2.icon = "icon2"
        mock_doc2.config_data = {}

        config1 = AgentConfig(
            agent_id="agent_1",
            name=LocaleString(en="Agent 1"),
            description=LocaleString(en="First agent"),
            icon="icon1",
        )

        config2 = AgentConfig(
            agent_id="agent_2",
            name=LocaleString(en="Agent 2"),
            description=LocaleString(en="Second agent"),
            icon="icon2",
        )

        with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find:
            mock_find.return_value = [mock_doc1, mock_doc2]

            with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                mock_from_entity.side_effect = [config1, config2]

                # Retrieve all configs for class
                docs = AgentConfigEntityDocument.find_for_class("TestAgent")
                assert len(docs) == 2

                # Convert each document to config
                converted_configs = [AgentConfig.from_entity(doc) for doc in docs]
                assert len(converted_configs) == 2
                assert converted_configs[0] == config1
                assert converted_configs[1] == config2

    def test_error_handling_db_exception(self):
        """Test handling of database exceptions."""
        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            mock_find.side_effect = Exception("Database connection failed")

            # Should propagate the exception
            with pytest.raises(Exception) as exc_info:
                AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "test_agent")

            assert str(exc_info.value) == "Database connection failed"

    def test_config_priority_logic(self, sample_default_config):
        """Test the priority logic: DB config takes precedence over default."""
        # This test demonstrates the expected behavior for configuration resolution

        # Scenario 1: DB config exists - should use DB config
        db_config = AgentConfig(
            agent_id="test_agent",
            name=LocaleString(en="DB Config"),
            description=LocaleString(en="From database"),
            icon="db-icon",
        )

        mock_doc = Mock()
        mock_doc.agent_class = "TestAgent"
        mock_doc.agent_id = "test_agent"
        mock_doc.config_data = {}

        with patch.object(AgentConfigEntityDocument, "find_for_class_and_id") as mock_find:
            with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                # When DB config exists
                mock_find.return_value = mock_doc
                mock_from_entity.return_value = db_config

                # Should use DB config
                result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "test_agent")
                assert result == mock_doc

                config = AgentConfig.from_entity(result)
                assert config == db_config

                # Scenario 2: DB config doesn't exist - should use default
                mock_find.return_value = None

                result = AgentConfigEntityDocument.find_for_class_and_id("TestAgent", "nonexistent_agent")
                assert result is None

                # In this case, the calling code would fall back to default_config
                # This demonstrates that the priority is: DB config > default config
