from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber, LocaleInput
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class LLMWrappingAgentConfig(AgentConfig):
    """
    Configuration for LLMWrappingAgent.

    Supports duality pattern for form rendering and data validation.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput,
        Field(description="System prompt that sets the agent's behaviour for the wrapped LLM."),
    ]
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
