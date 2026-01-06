from typing import Annotated

import pytest
from pydantic import BaseModel, Field, ValidationError

from aihub_lib.agents.AgentConfig import AgentConfig, StepConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import Checkbox, InputNumber, InputText
from aihub_lib.persistence.agents.AgentConfigEntityEmbeddedDocument import AgentConfigEntityEmbeddedDocument
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity


@pytest.fixture
def sample_locale_string() -> LocaleString:
    """Sample multi-language string for testing."""
    return LocaleString(
        de="Test Agent",
        en="Test Agent",
        fr="Agent de test",
        it="Agente di prova",
    )


@pytest.fixture
def sample_agent_config_entity(sample_locale_string: LocaleString) -> AgentConfigEntityEmbeddedDocument:
    """Agent config entity with nested dictionary structure."""
    return AgentConfigEntityEmbeddedDocument(
        agent_class="NestedAgent",
        agent_id="nested-agent-1",
        name=LocaleStringEntity.from_locale_string(sample_locale_string),
        description=LocaleStringEntity.from_locale_string(sample_locale_string),
        icon="meteor-icons:nested",
        config_data={
            "api_endpoint": "https://api.example.com",
            "retry_config": {
                "max_retries": 5,
                "backoff_multiplier": 2.0,
                "enabled": True,
            },
            "llm_settings": {
                "model_name": "gpt-4",
                "temperature": 0.8,
            },
        },
    )


class TestAgentConfig:
    """Test cases for AgentConfig class."""

    def test_agent_config_creation_with_required_fields(self, sample_locale_string: LocaleString) -> None:
        """Test that AgentConfig can be created with required fields."""
        config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
        )

        assert config.agent_class == "TestAgent"
        assert config.agent_id == "test-agent-1"
        assert config.name == sample_locale_string
        assert config.description == sample_locale_string
        assert config.icon == "meteor-icons:robot"  # Default value

    def test_agent_config_with_custom_icon(self, sample_locale_string: LocaleString) -> None:
        """Test that AgentConfig accepts custom icon."""
        config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
            icon="meteor-icons:custom",
        )

        assert config.icon == "meteor-icons:custom"

    def test_agent_id_validation_pattern(self, sample_locale_string: LocaleString) -> None:
        """Test that agent_id pattern validation works correctly."""
        # Valid IDs
        valid_ids = ["test-agent-1", "agent_123", "my-custom-agent", "a", "agent-1-2-3"]
        for agent_id in valid_ids:
            config = AgentConfig(
                agent_class="TestAgent",
                agent_id=agent_id,
                name=sample_locale_string,
                description=sample_locale_string,
            )
            assert config.agent_id == agent_id

        # Invalid IDs (uppercase, spaces, special chars)
        invalid_ids = ["Test-Agent", "agent 1", "agent.1", "AGENT_123", "agent@1"]
        for agent_id in invalid_ids:
            with pytest.raises(ValidationError):
                AgentConfig(
                    agent_class="TestAgent",
                    agent_id=agent_id,
                    name=sample_locale_string,
                    description=sample_locale_string,
                )

    def test_agent_config_extra_fields_allowed(self, sample_locale_string: LocaleString) -> None:
        """Test that AgentConfig accepts extra fields due to extra='allow'."""
        config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
            custom_field="custom_value",
            api_endpoint="https://api.example.com",
        )

        assert config.custom_field == "custom_value"  # type: ignore[attr-defined]
        assert config.api_endpoint == "https://api.example.com"  # type: ignore[attr-defined]

    def test_from_entity_simple(self, sample_agent_config_entity: AgentConfigEntityEmbeddedDocument) -> None:
        """Test creating AgentConfig from entity with simple config_data."""
        config = AgentConfig.from_entity(sample_agent_config_entity)

        assert config.agent_class == "NestedAgent"
        assert config.agent_id == "nested-agent-1"
        assert config.name.de == "Test Agent"
        assert config.description.en == "Test Agent"
        assert config.icon == "meteor-icons:nested"

    def test_from_entity_with_nested_config(
        self, sample_agent_config_entity: AgentConfigEntityEmbeddedDocument
    ) -> None:
        """Test that from_entity correctly unpacks nested config_data."""
        config = AgentConfig.from_entity(sample_agent_config_entity)

        # Nested config should be accessible as attributes
        assert config.api_endpoint == "https://api.example.com"  # type: ignore[attr-defined]
        assert config.retry_config == {  # type: ignore[attr-defined]
            "max_retries": 5,
            "backoff_multiplier": 2.0,
            "enabled": True,
        }
        assert config.llm_settings == {  # type: ignore[attr-defined]
            "model_name": "gpt-4",
            "temperature": 0.8,
        }

    def test_recursive_formkit_from_dict_simple_types(self) -> None:
        """Test recursive_formkit_from_dict with simple primitive types."""
        config_dict = {
            "api_key": "secret123",
            "max_retries": 3,
            "timeout": 30.5,
            "enabled": True,
        }

        model_class = AgentConfig.recursive_formkit_from_dict("SimpleConfig", config_dict)
        # Instantiate the model to access the fields
        model = model_class()

        assert hasattr(model, "api_key")
        assert hasattr(model, "max_retries")
        assert hasattr(model, "timeout")
        assert hasattr(model, "enabled")

        # Check default values
        assert model.api_key == "secret123"
        assert model.max_retries == 3
        assert model.timeout == 30.5
        assert model.enabled is True

    def test_recursive_formkit_from_dict_nested_structure(self) -> None:
        """Test recursive_formkit_from_dict with nested dictionaries."""
        config_dict = {
            "api_endpoint": "https://api.example.com",
            "retry_config": {
                "max_retries": 5,
                "backoff_multiplier": 2.0,
                "enabled": True,
            },
        }

        model_class = AgentConfig.recursive_formkit_from_dict("NestedConfig", config_dict)
        model = model_class()

        assert hasattr(model, "api_endpoint")
        assert hasattr(model, "retry_config")
        assert model.api_endpoint == "https://api.example.com"

        nested = model.retry_config
        assert isinstance(nested, BaseModel)
        assert nested.max_retries == 5
        assert nested.backoff_multiplier == 2.0
        assert nested.enabled is True

    def test_recursive_formkit_from_dict_deeply_nested(self) -> None:
        """Test recursive_formkit_from_dict with deeply nested structures."""
        config_dict = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep_value",
                        "count": 42,
                    }
                }
            }
        }

        model_class = AgentConfig.recursive_formkit_from_dict("DeepConfig", config_dict)
        model = model_class()

        assert hasattr(model, "level1")
        assert isinstance(model.level1, BaseModel)
        assert isinstance(model.level1.level2, BaseModel)
        assert isinstance(model.level1.level2.level3, BaseModel)
        assert model.level1.level2.level3.value == "deep_value"
        assert model.level1.level2.level3.count == 42

    def test_formkit_from_entity(self, sample_agent_config_entity: AgentConfigEntityEmbeddedDocument) -> None:
        """Test formkit_from_entity creates correct model structure."""
        model_class = AgentConfig.formkit_from_entity(sample_agent_config_entity)
        model = model_class()

        assert hasattr(model, "api_endpoint")
        assert hasattr(model, "retry_config")
        assert hasattr(model, "llm_settings")

        assert isinstance(model.retry_config, BaseModel)
        assert model.retry_config.max_retries == 5
        assert model.retry_config.backoff_multiplier == 2.0
        assert model.retry_config.enabled is True

        assert isinstance(model.llm_settings, BaseModel)
        assert model.llm_settings.model_name == "gpt-4"
        assert model.llm_settings.temperature == 0.8

    def test_formkit_from_entity_generates_formkit_types(
        self, sample_agent_config_entity: AgentConfigEntityEmbeddedDocument
    ) -> None:
        """Test that formkit_from_entity generates FormKit UI element types, not just plain values."""
        model_class = AgentConfig.formkit_from_entity(sample_agent_config_entity)
        model = model_class()

        assert isinstance(model.api_endpoint, str | InputText)

        assert isinstance(model.retry_config.max_retries, int | InputNumber)

        assert isinstance(model.retry_config.backoff_multiplier, float | InputNumber)

        assert isinstance(model.retry_config.enabled, bool | Checkbox)

        assert isinstance(model.llm_settings.model_name, str | InputText)

        assert isinstance(model.llm_settings.temperature, float | InputNumber)


class TestStepConfig:
    """Test cases for StepConfig functionality."""

    def test_step_config_basic(self) -> None:
        """Test that StepConfig can be instantiated."""
        step_config = StepConfig()
        assert isinstance(step_config, StepConfig)

    def test_custom_step_config_with_fields(self) -> None:
        """Test custom StepConfig with fields."""

        class CustomStepConfig(StepConfig):
            timeout: int = 30
            retry_enabled: bool = True
            model_name: str = "gpt-4"

        config = CustomStepConfig(timeout=60, retry_enabled=False)
        assert config.timeout == 60
        assert config.retry_enabled is False
        assert config.model_name == "gpt-4"  # Default

    def test_get_step_configs_empty(self, sample_locale_string: LocaleString) -> None:
        """Test get_step_configs returns empty dict when no step configs present."""
        config = AgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
        )

        step_configs = config.get_step_configs()
        assert step_configs == {}

    def test_get_step_configs_with_step_configs(self, sample_locale_string: LocaleString) -> None:
        """Test get_step_configs returns step configs correctly."""

        class StepAConfig(StepConfig):
            setting_a: str = "value_a"

        class StepBConfig(StepConfig):
            setting_b: int = 42

        class CustomAgentConfig(AgentConfig):
            step_a: StepAConfig = Field(default_factory=lambda: StepAConfig())
            step_b: StepBConfig = Field(default_factory=lambda: StepBConfig())
            regular_field: str = "not_a_step_config"

        config = CustomAgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
        )

        step_configs = config.get_step_configs()

        assert len(step_configs) == 2
        assert StepAConfig in step_configs
        assert StepBConfig in step_configs
        assert isinstance(step_configs[StepAConfig], StepAConfig)
        assert isinstance(step_configs[StepBConfig], StepBConfig)

    def test_get_step_configs_retrieves_correct_instances(self, sample_locale_string: LocaleString) -> None:
        """Test that get_step_configs returns the actual instances."""

        class ProcessingConfig(StepConfig):
            max_items: int = 100

        class CustomAgentConfig(AgentConfig):
            processing: ProcessingConfig = Field(default_factory=lambda: ProcessingConfig(max_items=200))

        config = CustomAgentConfig(
            agent_class="TestAgent",
            agent_id="test-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
        )

        step_configs = config.get_step_configs()
        processing_config = step_configs[ProcessingConfig]
        assert processing_config.max_items == 200


class TestAgentConfigFormIntegration:
    """Test cases for AgentConfig Form integration."""

    def test_agent_config_with_form_elements(self, sample_locale_string: LocaleString) -> None:
        """Test that AgentConfig can include FormKit elements."""

        class FormAgentConfig(AgentConfig):
            api_key: Annotated[str | InputText, Field(description="API Key")]
            max_tokens: Annotated[int | InputNumber, Field(description="Maximum tokens")]
            enable_logging: Annotated[bool | Checkbox, Field(description="Enable logging")]

        config = FormAgentConfig(
            agent_class="FormAgent",
            agent_id="form-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
            api_key=InputText(label="API Key"),
            max_tokens=InputNumber(label="Max Tokens", min_value=1, max_value=4000),
            enable_logging=Checkbox(label="Enable Logging"),
        )

        # Verify form elements are properly assigned
        assert isinstance(config.api_key, InputText)
        assert isinstance(config.max_tokens, InputNumber)
        assert isinstance(config.enable_logging, Checkbox)

    def test_to_formkit_form_generates_elements(self, sample_locale_string: LocaleString) -> None:
        """Test that to_formkit_form() generates correct FormKit elements."""

        class FormAgentConfig(AgentConfig):
            api_key: Annotated[str | InputText, Field(description="API Key")]
            max_tokens: Annotated[int | InputNumber, Field(description="Maximum tokens")]
            enable_logging: Annotated[bool | Checkbox, Field(description="Enable logging")]

        config = FormAgentConfig(
            agent_class="FormAgent",
            agent_id="form-agent-1",
            name=sample_locale_string,
            description=sample_locale_string,
            api_key=InputText(label="API Key"),
            max_tokens=InputNumber(label="Max Tokens", min_value=1, max_value=4000),
            enable_logging=Checkbox(label="Enable Logging"),
        )

        form_elements = config.to_formkit_form()

        # Should generate form elements for the FormKit fields
        assert len(form_elements) >= 3
        element_names = [elem.name for elem in form_elements]
        assert "api_key" in element_names
        assert "max_tokens" in element_names
        assert "enable_logging" in element_names


class TestAgentConfigEntityRoundTrip:
    """Test round-trip conversion between AgentConfig and AgentConfigEntity."""

    def test_entity_to_config_to_entity(
        self, sample_locale_string: LocaleString, sample_agent_config_entity: AgentConfigEntityEmbeddedDocument
    ) -> None:
        """Test converting entity → config → entity preserves data."""
        # Entity to Config
        config = AgentConfig.from_entity(sample_agent_config_entity)

        # Config back to Entity
        new_entity = AgentConfigEntityEmbeddedDocument.from_agent_config(config)

        # Verify core fields match
        assert new_entity.agent_class == sample_agent_config_entity.agent_class
        assert new_entity.agent_id == sample_agent_config_entity.agent_id
        assert new_entity.icon == sample_agent_config_entity.icon

        # Verify config_data contains original nested structure
        assert "api_endpoint" in new_entity.config_data
        assert "retry_config" in new_entity.config_data
        assert "llm_settings" in new_entity.config_data
