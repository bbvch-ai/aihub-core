from typing import Annotated, Any, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.form import Checkbox, InputNumber, LocaleInput
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import LLMConfig, usable_input_budget
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ConversationFields(Form):
    """
    What every chat blueprint configures: the answering model, the auxiliary model, the input budget and
    whether the turn's query is condensed out of the history.

    A form mixin, not a config: a blueprint's `AgentConfig` lists it as a base next to the fields of the
    other capabilities it installs, and the dispatcher injects the concrete config into any step parameter
    annotated with it. Subclasses that need other defaults override the field.
    """

    system_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(description="System prompt to guide the agent's behavior and responses.", title="System Prompt"),
    ] = None
    llm: Annotated[
        LLMConfig,
        Field(description="The LLM configuration for the agent."),
    ]
    task_llm: Annotated[
        LLMConfig | None,
        Field(
            default=None,
            description=(
                "Model for this agent's auxiliary steps: meta-question detection and answering, "
                "standalone-question condensation, guards, and conversation title plus follow-up question "
                "generation. Generation parameters are inherited from the main model. Falls back to the main "
                "model when disabled."
            ),
            title="Task LLM",
        ),
    ] = None
    number_of_input_tokens: Annotated[
        int | InputNumber,
        Field(description="Maximum tokens allowed in input to manage context size or cost."),
        Gt(0),
    ] = 128000
    condense_question: Annotated[
        bool | Checkbox,
        Field(
            description=(
                "Condense the conversation into one standalone question before enrichment and retrieval. "
                "Off means the last user message is the query as is."
            ),
        ),
    ] = False

    def input_budget(self) -> int:
        """The admin's cost ceiling capped by the narrowest model window that could receive the prompt."""
        budget = usable_input_budget([self.llm, self.task_llm])
        return self.number_of_input_tokens if budget is None else min(self.number_of_input_tokens, budget)

    @model_validator(mode="after")
    def derive_task_llm_from_main_llm(self) -> Self:
        """Only the task model is configurable: its generation parameters always mirror the main llm, and
        an unset or blank picker falls back to the main model."""
        if not isinstance(self.llm.model_name, str):
            return self
        task_model_name = self.task_llm.model_name if self.task_llm else None
        self.task_llm = self.llm.as_task_llm(task_model_name or self.llm.model_name)
        return self

    @classmethod
    def conversation_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {
            "llm": LLMConfig.as_form(),
            "task_llm": LLMConfig.as_form(include_default_parameter=False),
            "number_of_input_tokens": InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.conversation.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation.config.number_of_input_tokens.help"),
                min=1024,
                max=200000,
                step=1024,
            ),
            "condense_question": Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.conversation.config.condense_question.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation.config.condense_question.help"),
            ),
        }
