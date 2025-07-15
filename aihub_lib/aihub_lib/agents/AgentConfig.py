import json
import logging
from typing import Annotated, Any, TYPE_CHECKING, ClassVar

from pydantic import BaseModel, Field, PrivateAttr, ConfigDict, computed_field
from typing_extensions import override

from aihub_lib.i18n.LocaleString import LocaleString

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


class AgentConfig(BaseModel):
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

    _config_registry: ClassVar[dict[str, type["AgentConfig"]]] = {}

    agent_class: Annotated[str, Field(description="The class name of the agent, used for identification.")]
    agent_id: Annotated[str, Field(description="Uniquely identifies the agent instance.", pattern=r"^[a-z0-9_-]+$")]
    name: Annotated[LocaleString, Field(description="The name of the agent.")]
    description: Annotated[LocaleString, Field(description="The description of the agent.")]
    icon: Annotated[str, Field(description="The icon representing the agent.")] = "meteor-icons:robot"

    color: Annotated[
        str | None,
        Field(
            description="The color of the agent UI theme.",
            deprecated="This field is deprecated. It will be removed in a future release. "
            "If you need a color, please define it yourself in a subclass of AgentConfig.",
        ),
    ] = "#10A37F"
    voice: Annotated[
        str | None,
        Field(
            description="The TTS voice ID the agent uses.",
            deprecated="This field is deprecated. It will be removed in a future release. "
            "If you need a voice, please define it yourself in a subclass of AgentConfig.",
        ),
    ] = "de-DE-ChristophNeural"
    system_prompt: Annotated[
        LocaleString,
        Field(
            description="The system prompt of the agent.",
            deprecated="This field is deprecated. It will be removed in a future release."
            "If you need a system prompt, please define it yourself in a subclass of AgentConfig.",
        ),
    ]

    # Private attributes to handle unknown config types
    _unknown_config_name: str | None = PrivateAttr(None)
    _unknown_data: dict[str, Any] | None = PrivateAttr(None)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    def __str__(self):
        return f"{self.config_name}({super().__str__()})"

    @classmethod
    def config_name_from_class(cls) -> str:
        return cls.__name__

    def parent_config(self, parent_type: type["AgentConfig"]) -> "AgentConfig":
        if self._unknown_data is None or self._unknown_config_name is None:
            raise ValueError("Cannot retrieve parent config without unknown data or config name.")
        if not parent_type.config_name_from_class() == self._unknown_config_name:
            raise ValueError(
                f"Cannot retrieve parent config of type {parent_type.__name__} from {self._unknown_config_name}"
            )
        return parent_type(**self._unknown_data)

    @classmethod
    def from_entity(cls, entity: "AgentConfigEntity") -> "AgentConfig":
        config = cls(
            agent_class=entity.agent_class,
            agent_id=entity.agent_id,
            name=entity.name.to_locale_string(),
            description=entity.description.to_locale_string(),
            icon=entity.icon,
            color=entity.color,  # Default color if not set
            voice=entity.voice,
            system_prompt=entity.system_prompt.to_locale_string(),
        )
        config._unknown_config_name = entity.agent_class
        config._unknown_data = entity.config_data
        return config

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

    @computed_field
    @property
    def _config_name(self) -> str:
        return self._unknown_config_name or self.__class__.__name__

    @property
    def config_name(self) -> str:
        return self._config_name

    @override
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """
        Serializes the config into a dictionary. If this config was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        data = super().model_dump(**kwargs)
        if self._unknown_data is None:
            return data

        return {
            **self._unknown_data,
            **data,
        }

    @override
    def model_dump_json(self, **kwargs: Any) -> str:
        """
        Serializes the event into a JSON string. If this event was originally unknown,
        merges the original data with the known fields so nothing is lost.
        """
        return json.dumps(self.model_dump(**kwargs), default=str)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """
        Called when a new subclass is defined, registering it in the _event_registry.
        This makes dynamic deserialization possible.
        """
        super().__pydantic_init_subclass__(**kwargs)
        logger.debug(f"Registering Config {cls.__name__}")
        if cls.__name__ in AgentConfig._config_registry:
            raise ValueError(f"Duplication detected for Config {cls.__name__}")
        AgentConfig._config_registry[cls.__name__] = cls

    @classmethod
    def deserialize_config(cls, data: bytes | str | dict[str, Any]) -> "AgentConfig":
        """
        Given raw config data, deserializes it into the specific AgentConfig type.
        """
        if isinstance(data, dict):
            json_data = data.copy()
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        config_name = json_data.get("_config_name")

        if config_name and isinstance(config_name, str):
            config_class = cls._config_registry.get(config_name)
            if config_class:
                logger.debug(f"Deserializing {config_name} config")
                return config_class(**json_data)

        # If we get here, either:
        # 1. The event type wasn't in our registry, or
        # 2. The event type was null/invalid
        logger.debug(f"Unknown config type: {config_name}")
        event = cls(**json_data)
        event._unknown_config_name = config_name
        event._unknown_data = json_data
        return event
