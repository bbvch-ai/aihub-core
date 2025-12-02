from unittest.mock import Mock, patch

import pytest
from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.infrastructure.logging.logger import enable_logging
from fastapi import HTTPException

from aihub_api.routes.agent.AgentService import GET_AGENT_INSTANCE_CACHE, AgentService
from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO

enable_logging()


@pytest.fixture(autouse=True)
def cleanup_db_and_cache(sample_agent_config):
    AgentService._clear_cache()
    yield
    AgentService._clear_cache()


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
def sample_default_config():
    """Create a sample default AgentConfig for testing."""
    return AgentConfig(
        agent_class="TestAgent",
        agent_id="default_agent",
        name=LocaleString(en="Default Test Agent"),
        description=LocaleString(en="Default test agent configuration"),
        icon="default-icon",
    )


@pytest.fixture
def sample_agent_class(sample_default_config):
    """Create a sample AgentClass with default config."""
    mock_agent_class = Mock(spec=AgentClassDTO)
    mock_agent_class.agent_class = "TestAgent"
    mock_agent_class.default_agent_config = sample_default_config
    return mock_agent_class


@pytest.fixture
def mock_agent_config_document(sample_agent_config):
    """Create a mock AgentConfigEntityDocument."""
    mock_doc = Mock()
    mock_doc.agent_class = sample_agent_config.agent_class
    mock_doc.agent_id = sample_agent_config.agent_id
    mock_doc.name = sample_agent_config.name
    mock_doc.description = sample_agent_config.description
    mock_doc.icon = sample_agent_config.icon
    mock_doc.config_data = {}
    return mock_doc


@pytest.fixture
def mock_nats():
    """Create a mock NATS connection."""
    return Mock()


class TestAgentServiceDatabaseIntegration:
    """Test AgentService database integration and config override logic."""

    @pytest.mark.asyncio
    async def test_discover_agent_instance_with_db_config(
        self, mock_nats, sample_agent_config, sample_agent_class, mock_agent_config_document
    ):
        """Test that AgentService.discover_agent_instance correctly fetches and uses DB config."""
        # Clear any existing cache
        AgentService._clear_cache()

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_agent_config_document]

                with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = sample_agent_config

                    with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=AgentInstanceDTO)
                        mock_instance.agent_config = sample_agent_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await AgentService.discover_agent_instance(
                            nc=mock_nats, agent_class="TestAgent", agent_id="test_agent_1"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                        mock_find_configs.assert_called_once_with("TestAgent")
                        mock_from_entity.assert_called_once_with(mock_agent_config_document)
                        mock_from_class_config.assert_called_once_with(
                            class_dto=sample_agent_class, agent_config=sample_agent_config
                        )

                        # Verify the result
                        assert result == mock_instance
                        assert result.agent_config == sample_agent_config

    @pytest.mark.asyncio
    async def test_discover_agent_instance_fallback_to_default(
        self, mock_nats, sample_default_config, sample_agent_class
    ):
        """Test that AgentService.discover_agent_instance falls back to default config when no DB config exists."""
        # Clear any existing cache
        AgentService._clear_cache()

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                    mock_instance = Mock(spec=AgentInstanceDTO)
                    mock_instance.agent_config = sample_default_config
                    mock_from_class_config.return_value = mock_instance

                    # Execute the method
                    result = await AgentService.discover_agent_instance(
                        nc=mock_nats, agent_class="TestAgent", agent_id="default_agent"
                    )

                    # Verify the flow
                    mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                    mock_find_configs.assert_called_once_with("TestAgent")
                    mock_from_class_config.assert_called_once_with(
                        class_dto=sample_agent_class, agent_config=sample_default_config
                    )

                    # Verify the result uses default config
                    assert result == mock_instance
                    assert result.agent_config == sample_default_config

    @pytest.mark.asyncio
    async def test_discover_agent_instance_db_config_overrides_default(
        self, mock_nats, sample_agent_class, mock_agent_config_document
    ):
        """Test that DB config overrides default config when both have the same agent_id."""
        # Clear any existing cache
        AgentService._clear_cache()

        # Create a DB config with same ID as default
        db_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="default_agent",  # Same ID as default
            name=LocaleString(en="DB Override Config"),
            description=LocaleString(en="DB config overriding default"),
            icon="db-icon",
        )

        # Mock the document to have the same ID as default
        mock_agent_config_document.agent_id = "default_agent"

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_agent_config_document]

                with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config

                    with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=AgentInstanceDTO)
                        mock_instance.agent_config = db_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await AgentService.discover_agent_instance(
                            nc=mock_nats, agent_class="TestAgent", agent_id="default_agent"
                        )

                        # Verify the flow - should use DB config, not default
                        mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                        mock_find_configs.assert_called_once_with("TestAgent")
                        mock_from_entity.assert_called_once_with(mock_agent_config_document)
                        mock_from_class_config.assert_called_once_with(
                            class_dto=sample_agent_class,
                            agent_config=db_config,  # Should use DB config, not default
                        )

                        # Verify the result uses DB config
                        assert result == mock_instance
                        assert result.agent_config == db_config
                        assert result.agent_config.name.en == "DB Override Config"

    @pytest.mark.asyncio
    async def test_discover_agent_instance_not_found(self, mock_nats, sample_agent_class):
        """Test that AgentService.discover_agent_instance raises 404 when agent not found."""
        # Clear any existing cache
        AgentService._clear_cache()

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                # Execute the method with non-existent agent_id
                with pytest.raises(HTTPException) as exc_info:
                    await AgentService.discover_agent_instance(
                        nc=mock_nats, agent_class="TestAgent", agent_id="nonexistent_agent"
                    )

                # Verify the exception
                assert exc_info.value.status_code == 404
                assert "Agent TestAgent.nonexistent_agent not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_discover_agent_instances_by_class_with_db_and_default(
        self, mock_nats, sample_agent_class, mock_agent_config_document, sample_agent_config, sample_default_config
    ):
        """Test that AgentService.discover_agent_instances_by_class includes both DB and default configs."""
        # Clear any existing cache
        AgentService._clear_cache()

        # Create a second DB config with different ID
        mock_doc2 = Mock()
        mock_doc2.agent_class = "TestAgent"
        mock_doc2.agent_id = "db_agent_2"
        mock_doc2.name = LocaleString(en="DB Agent 2")
        mock_doc2.description = LocaleString(en="Second DB agent")
        mock_doc2.icon = "db-icon2"
        mock_doc2.config_data = {}

        config2 = AgentConfig(
            agent_class="TestAgent",
            agent_id="db_agent_2",
            name=LocaleString(en="DB Agent 2"),
            description=LocaleString(en="Second DB agent"),
            icon="db-icon2",
        )

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_agent_config_document, mock_doc2]

                with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.side_effect = [sample_agent_config, config2]

                    with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance1 = Mock(spec=AgentInstanceDTO)
                        mock_instance1.agent_config = sample_agent_config
                        mock_instance2 = Mock(spec=AgentInstanceDTO)
                        mock_instance2.agent_config = config2
                        mock_instance3 = Mock(spec=AgentInstanceDTO)
                        mock_instance3.agent_config = sample_default_config

                        mock_from_class_config.side_effect = [mock_instance1, mock_instance2, mock_instance3]

                        # Execute the method
                        result = await AgentService.discover_agent_instances_by_class(
                            nc=mock_nats, agent_class="TestAgent"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                        mock_find_configs.assert_called_once_with("TestAgent")
                        assert mock_from_entity.call_count == 2
                        assert mock_from_class_config.call_count == 3  # 2 DB configs + 1 default

                        # Verify the result includes all configs
                        assert len(result) == 3
                        agent_ids = [instance.agent_config.agent_id for instance in result]
                        assert "test_agent_1" in agent_ids
                        assert "db_agent_2" in agent_ids
                        assert "default_agent" in agent_ids

    @pytest.mark.asyncio
    async def test_discover_agent_instances_by_class_excludes_default_when_db_has_same_id(
        self, mock_nats, sample_agent_class, mock_agent_config_document, sample_default_config
    ):
        """Test that default config is excluded when DB has config with same agent_id."""
        # Clear any existing cache
        AgentService._clear_cache()

        # Create DB config with same ID as default
        db_config = AgentConfig(
            agent_class="TestAgent",
            agent_id="default_agent",  # Same ID as default
            name=LocaleString(en="DB Override Config"),
            description=LocaleString(en="DB config overriding default"),
            icon="db-icon",
        )

        mock_agent_config_document.agent_id = "default_agent"

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = [mock_agent_config_document]

                with patch.object(AgentConfig, "from_entity") as mock_from_entity:
                    mock_from_entity.return_value = db_config

                    with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                        mock_instance = Mock(spec=AgentInstanceDTO)
                        mock_instance.agent_config = db_config
                        mock_from_class_config.return_value = mock_instance

                        # Execute the method
                        result = await AgentService.discover_agent_instances_by_class(
                            nc=mock_nats, agent_class="TestAgent"
                        )

                        # Verify the flow
                        mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                        mock_find_configs.assert_called_once_with("TestAgent")
                        mock_from_entity.assert_called_once_with(mock_agent_config_document)
                        mock_from_class_config.assert_called_once()  # Only called once for DB config

                        # Verify the result includes only DB config, not default
                        assert len(result) == 1
                        assert result[0].agent_config == db_config
                        assert result[0].agent_config.name.en == "DB Override Config"

    @pytest.mark.asyncio
    async def test_discover_agent_instances_by_class_cache_behavior(self, mock_nats, sample_agent_class):
        """Test that AgentService.discover_agent_instances_by_class uses cache correctly."""
        # Clear any existing cache
        AgentService._clear_cache()

        cached_result = [Mock(spec=AgentInstanceDTO)]
        cache_key = ("TestAgent", "*")
        GET_AGENT_INSTANCE_CACHE[cache_key] = cached_result

        # Execute the method
        result = await AgentService.discover_agent_instances_by_class(nc=mock_nats, agent_class="TestAgent")

        # Verify cached result is returned
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_agent_instance_cache_behavior(self, mock_nats, sample_agent_class):
        """Test that AgentService.discover_agent_instance uses cache correctly."""
        # Clear any existing cache
        AgentService._clear_cache()

        cached_result = Mock(spec=AgentInstanceDTO)
        cache_key = ("TestAgent", "test_agent_1")
        GET_AGENT_INSTANCE_CACHE[cache_key] = cached_result

        # Execute the method
        result = await AgentService.discover_agent_instance(
            nc=mock_nats, agent_class="TestAgent", agent_id="test_agent_1"
        )

        # Verify cached result is returned
        assert result == cached_result

    @pytest.mark.asyncio
    async def test_discover_agent_instances_by_class_only_default_config(
        self, mock_nats, sample_agent_class, sample_default_config
    ):
        """Test that discover_agent_instances_by_class returns only default config when no DB configs exist."""
        # Clear any existing cache
        AgentService._clear_cache()

        with patch.object(AgentService, "_discover_agent_class") as mock_discover_class:
            mock_discover_class.return_value = sample_agent_class

            with patch.object(AgentConfigEntityDocument, "find_for_class") as mock_find_configs:
                mock_find_configs.return_value = []  # No DB configs found

                with patch.object(AgentInstanceDTO, "from_class_and_config") as mock_from_class_config:
                    mock_instance = Mock(spec=AgentInstanceDTO)
                    mock_instance.agent_config = sample_default_config
                    mock_from_class_config.return_value = mock_instance

                    # Execute the method
                    result = await AgentService.discover_agent_instances_by_class(nc=mock_nats, agent_class="TestAgent")

                    # Verify the flow
                    mock_discover_class.assert_called_once_with(mock_nats, "TestAgent")
                    mock_find_configs.assert_called_once_with("TestAgent")
                    mock_from_class_config.assert_called_once_with(
                        class_dto=sample_agent_class, agent_config=sample_default_config
                    )

                    # Verify the result includes only the default config
                    assert len(result) == 1
                    assert result[0].agent_config == sample_default_config
