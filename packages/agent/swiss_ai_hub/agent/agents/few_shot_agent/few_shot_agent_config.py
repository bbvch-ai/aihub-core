from typing import Annotated, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.form import InputNumber
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.generative_ai import LLMConfig

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.steps.prompting.few_shot_step.few_shot_step_config import FewShotStepConfig


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
    task_llm: Annotated[
        LLMConfig | None,
        Field(
            default=None,
            description=(
                "Task LLM used for auxiliary tasks like standalone-question condensation, context/few-shot "
                "guards, meta-question detection, LLM routing, and conversation title + follow-up question "
                "generation. Falls back to the main LLM when disabled."
            ),
            title="Task LLM",
        ),
    ] = None
    few_shot: Annotated[
        FewShotStepConfig,
        Field(description="Few-shot prompting configuration with examples."),
    ]
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
        Gt(0),
    ] = 100000

    @model_validator(mode="after")
    def default_task_llm_to_main_llm(self) -> Self:
        """Auxiliary steps read `task_llm` directly, so an unset or blank picker falls back to the main llm."""
        if self.task_llm is None or not self.task_llm.model_name:
            self.task_llm = self.llm
        return self

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
            task_llm=LLMConfig.as_form(),
            few_shot=FewShotStepConfig.as_form(),
            number_of_input_tokens=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.few_shot_agent.config.number_of_input_tokens.help"),
                min=1000,
                max=200000,
                step=1000,
            ),
        )
