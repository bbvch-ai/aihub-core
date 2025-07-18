from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString


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
