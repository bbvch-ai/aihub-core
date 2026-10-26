from typing import Annotated, Any, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.form import Checkbox, LocaleInput, ModelBoundInputNumber
from swiss_ai_hub.core.form.constraints import Gt
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.generative_ai import LLMConfig, usable_input_budget
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

# Prompts are measured with tiktoken, not the served model's tokenizer, and a budget that is filled to the brim must
# absorb the difference: measured live, Ministral counts English 6% above tiktoken and gemma 4%, which overflowed a
# context-sufficiency prompt fitted exactly to the window (issue #2077). Same value as core's
# SUMMARIZATION_BUDGET_SAFETY_FACTOR and the mailbox agents' BUDGET_SAFETY_FACTOR.
WINDOW_SAFETY_FACTOR = 0.85
# What an unset limit fills when no model window can be established: the value every profile was created with
# before the limit followed the model.
FALLBACK_INPUT_TOKENS = 128000


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
        int | None | ModelBoundInputNumber,
        Field(
            description="The admin's own limit on the input tokens, to manage cost. None fills the models' input "
            "window (`input_budget`); a value is bounded by the main model's window when saved, and one stored above "
            "it is capped at run time."
        ),
        Gt(0),
    ] = None
    condense_question: Annotated[
        bool | Checkbox,
        Field(
            description=(
                "Condense the conversation into one standalone question before enrichment and retrieval. "
                "Off means the last user message is the query as is."
            ),
        ),
    ] = False

    @property
    def input_budget(self) -> int:
        """The narrowest model window that could receive the prompt, less a margin for the tokenizer difference, and
        held to the admin's own limit when one is set. Only for prompts that are filled to it; refusing an oversized
        message compares against the exact window (`do_limit_chat_history`), so nothing the model accepts is refused.

        A plain property, not a `computed_field`: it must stay out of `model_dump`, which also serializes the form-mode
        instance, and it looks the model window up in LiteLLM."""
        budget = usable_input_budget([self.llm, self.task_llm])
        if budget is None:
            return self.input_ceiling
        return self.held_to_ceiling(int(budget * WINDOW_SAFETY_FACTOR))

    @property
    def input_ceiling(self) -> int:
        """The admin's own limit, or `FALLBACK_INPUT_TOKENS` when none is set, for when no window is known."""
        return FALLBACK_INPUT_TOKENS if self.number_of_input_tokens is None else self.number_of_input_tokens

    def held_to_ceiling(self, tokens: int) -> int:
        """`tokens` held to the admin's own limit; with none set, the model window alone bounds the input."""
        return tokens if self.number_of_input_tokens is None else min(self.number_of_input_tokens, tokens)

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
            "number_of_input_tokens": ModelBoundInputNumber(
                label=AgentLocaleString.from_i18n_path("agent.conversation.config.number_of_input_tokens.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation.config.number_of_input_tokens.help"),
                override_label=AgentLocaleString.from_i18n_path(
                    "agent.conversation.config.number_of_input_tokens.toggle_label"
                ),
                model_ref="llm.model_name",
                max_from="max_input_tokens",
                fill_factor=WINDOW_SAFETY_FACTOR,
                fallback_default=FALLBACK_INPUT_TOKENS,
                min=1024,
                step=1024,
            ),
            "condense_question": Checkbox(
                label=AgentLocaleString.from_i18n_path("agent.conversation.config.condense_question.label"),
                help=AgentLocaleString.from_i18n_path("agent.conversation.config.condense_question.help"),
            ),
        }
