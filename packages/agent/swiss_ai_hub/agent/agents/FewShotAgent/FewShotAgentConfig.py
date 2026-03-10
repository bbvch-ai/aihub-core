from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents.AgentConfig import AgentConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from swiss_ai_hub.core.nats.events.form.constraints import Gt
from swiss_ai_hub.core.nats.events.form.elements.InputNumber import InputNumber

from swiss_ai_hub.agent.i18n.AgentLocaleString import AgentLocaleString
from swiss_ai_hub.agent.steps.prompting.few_shot_step.FewShotStepConfig import FewShotStepConfig


class FewShotAgentConfig(AgentConfig):
    """
    Configuration for FewShotAgent.

    This agent uses few-shot learning to guide its responses based on
    example user-agent interactions.

    Supports form duality pattern for form rendering and data validation.
    """

    llm: Annotated[
        LLMConfig,
        Field(description="LLM configuration for the agent."),
    ]
    few_shot: Annotated[
        FewShotStepConfig,
        Field(description="Few-shot prompting configuration with examples."),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
        Gt(0),
    ] = 100000

    @classmethod
    def as_form(cls) -> Self:
        """Factory method to create a form-mode FewShotAgentConfig."""
        base = AgentConfig.as_form()

        return cls(
            agent_id=base.agent_id,
            name=base.name,
            description=base.description,
            icon=base.icon,
            llm=LLMConfig.as_form(),
            few_shot=FewShotStepConfig.as_form(),
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.help"),
                min=1000,
                max=200000,
                step=1000,
            ),
        )
