import logging
from types import UnionType
from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, ConfigDict, Field, create_model

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form.Form import Form

if TYPE_CHECKING:
    from aihub_lib.persistence.agents import AgentConfigEntity

logger = logging.getLogger(__name__)


class StepConfig(BaseModel):
    """
    A base configuration class for workflow steps, allowing future extensions
    to store custom configuration fields relevant to particular steps.

    ### Why StepConfig?
    As workflow steps become more complex, certain steps may require configuration
    parameters—time limits, thresholds, behavior toggles, etc. By deriving from
    StepConfig, each step can define its own configuration model.

    The `AgentConfig` can then hold instances of these step configurations,
    keyed by step type, allowing easy retrieval and management of step-specific settings.
    """

    pass


class AgentConfig(Form):
    """
    The agent config is a flexible way to configure the runtime behavior of an agent. It can ensure that two agents
    that follow the same workflow can still be configured to achieve different outcomes through a different
    set of configurations.

    Usually, you will want to inherit from this AgentConfig and pass it to your runner.
    The dispatcher will then flexibly inject the config into each step,
    giving you full control over the agent's runtime behavior.

    Note that you can also define configs for individual workflow steps! Simply by naming the attribute the same
    way as your step, and assigning it a value of type `StepConfig`, you can configure the step's behavior.

    ```python
    class StepXConfig(StepConfig):
        some_setting: str

    class MyCustomAgentConfig(AgentConfig):
        step_x: StepXConfig = StepXConfig(some_setting="some value")

    class MyAgent(Agent):
        @step()
        def step_x(self, step_x_config: StepXConfig):
            print(step_x_config.some_setting)
    ```
    """

    name: Annotated[LocaleString, Field(description="The name of the process or agent.")]
    description: Annotated[LocaleString, Field(description="The description of the process or agent.")]
    icon: Annotated[str, Field(description="The icon representing the process or agent.")] = "meteor-icons:robot"

    agent_class: Annotated[str, Field(description="The class name of the agent, used for identification.")]
    agent_id: Annotated[str, Field(description="Uniquely identifies the agent instance.", pattern=r"^[a-z0-9_-]+$")]

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @classmethod
    def from_entity(cls, entity: "AgentConfigEntity") -> "AgentConfig":
        data = {
            "agent_class": entity.agent_class,
            "agent_id": entity.agent_id,
            "name": entity.name.to_locale_string(),
            "description": entity.description.to_locale_string(),
            "icon": entity.icon,
            **entity.config_data,
        }
        config = cls(**data)
        return config

    @staticmethod
    def recursive_formkit_from_dict(model_name: str, model_dict: dict) -> BaseModel:
        # Import at runtime to avoid circular imports
        from aihub_lib.nats.events.form import Checkbox, InputNumber, InputText

        mapping: dict[type, UnionType] = {
            str: InputText | str,
            int: InputNumber | int,
            float: InputNumber | float,
            bool: Checkbox | bool,
        }

        fields: dict[str, tuple[UnionType | type[BaseModel], ...]] = {}
        for key, value in model_dict.items():
            value_type = type(value)

            # Map to FormKit element type, fallback to the primitive type
            if value_type in mapping:
                fields[key] = (mapping[value_type], value)
            elif value_type is dict:
                # Recursively create nested model class where dict values become field defaults
                # Then instantiate to get an object with those values
                nested_model_class = AgentConfig.recursive_formkit_from_dict(key, value)
                nested_instance = nested_model_class()
                fields[key] = (nested_model_class, nested_instance)
            else:
                # do nothing
                pass

        return create_model(model_name, **fields)

    @staticmethod
    def formkit_from_entity(entity: "AgentConfigEntity") -> "BaseModel":
        agent_config: dict[str, str | float | int | bool | dict] = entity.config_data

        return AgentConfig.recursive_formkit_from_dict(entity.agent_class, agent_config)

    def get_step_configs(self) -> dict[type[StepConfig], StepConfig]:
        """
        Scans all fields in this AgentConfig and collects any that are `StepConfig` instances.
        """
        step_configs = {}
        for field_name in self.model_fields.keys():
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, StepConfig):
                step_configs[type(field_value)] = field_value
        return step_configs
