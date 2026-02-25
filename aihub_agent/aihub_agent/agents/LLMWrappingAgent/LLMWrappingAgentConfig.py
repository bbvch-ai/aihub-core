from typing import Annotated, Self

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.form import InputNumber, LocaleInput
from aihub_lib.nats.events.form.constraints import Gt
from pydantic import Field

from aihub_agent.i18n.AgentLocaleString import AgentLocaleString


class LLMWrappingAgentConfig(AgentConfig):
    """
    Configuration for LLMWrappingAgent.

    Supports duality pattern for form rendering and data validation.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt that sets the context for few-shot learning."),
    ] = None
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
        Gt(0),
    ] = 100000
    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode LLMWrappingAgentConfig."""
        base = AgentConfig.as_form()
        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            system_prompt=LocaleInput(
                label=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.config.system_prompt.label"),
                help=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.config.system_prompt.help"),
                input_type="textarea",
                rows=3,
            ),
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.help"),
                min=1000,
                max=200000,
                step=1000,
            ),
            llm=LLMConfig.as_form(),
        )
