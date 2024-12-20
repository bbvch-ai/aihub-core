from typing import Optional, Dict, Type

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
    Describes the configuration for an agent, including its identity, prompts, and style.

    ### Why AgentConfig?
    An agent might need:
    - Basic metadata (ID, name, description).
    - System prompts defining its initial behavior.
    - UI attributes (color, voice) to influence how it's presented or how it speaks.

    Storing these in a structured configuration object makes it easy for other
    components—like frontends or orchestrators—to retrieve and apply these settings.

    ### Features
    - **Agent Identity:** `agent_id`, `name`, and `description` define who the agent is.
    - **Prompts & Voice:** `system_prompt` and `voice` control how the agent communicates.
    - **Color:** A HEX color code for UI theming.
    - **Step Configurations:** Dynamically retrieve all `StepConfig` instances attached to this agent.

    ### Example
    ```python
    config = AgentConfig(
        agent_id="agent_123",
        name=LocaleString(en="My Agent"),
        description=LocaleString(en="Handles user queries"),
        system_prompt=LocaleString(en="You are a helpful assistant."),
    )
    ```

    Retrieving step configs:
    ```python
    step_configs = config.get_step_configs()
    ```
    """

    agent_id: str = Field(..., description="The id of the agent.")
    name: LocaleString = Field(..., description="The name of the agent.")
    description: LocaleString = Field(..., description="The description of the agent.")
    system_prompt: LocaleString = Field(..., description="The system prompt of the agent.")
    color: Optional[str] = Field("#10A37F", description="The color of the agent UI theme.")
    voice: Optional[str] = Field("de-DE-ChristophNeural", description="The TTS voice ID the agent uses.")

    def get_step_configs(self) -> Dict[Type[StepConfig], StepConfig]:
        """
        Scans all fields in this AgentConfig and collects any that are `StepConfig` instances.

        Returns:
            A dictionary mapping StepConfig subclass types to their instantiated configurations.
        """
        step_configs = {}
        for field_name in self.model_fields.keys():
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, StepConfig):
                step_configs[type(field_value)] = field_value
        return step_configs
