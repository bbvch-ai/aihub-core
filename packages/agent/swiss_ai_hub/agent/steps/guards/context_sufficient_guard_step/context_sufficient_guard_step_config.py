from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.agents import StepConfig
from swiss_ai_hub.core.form import Checkbox, InputNumber, LocaleInput
from swiss_ai_hub.core.form.constraints import Ge
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class ContextSufficientGuardStepConfig(StepConfig):
    """Configuration for the context-sufficient guard step.

    Groups the settings that control whether and how the guard LLM evaluates if the
    retrieved context (plus recent conversation + injected memory) is enough to answer
    the user's question before generation.
    """

    check_context_sufficiency: Annotated[
        bool | Checkbox,
        Field(
            description="Whether to run the guard. When False, context is always treated as sufficient.",
        ),
    ] = False
    max_hops: Annotated[
        int | InputNumber,
        Field(
            description="Maximum number of retrieval iterations when the guard rejects the current context.",
        ),
        Ge(1),
    ] = 1
    max_non_system_messages_in_guard: Annotated[
        int | InputNumber,
        Field(
            description=(
                "Maximum number of recent user/assistant messages forwarded to the guard prompt. "
                "System messages (injected user/organization memory) are always kept. Lower values "
                "shorten the guard prompt and improve structured-output reliability for open-weight models."
            ),
        ),
        Ge(0),
    ] = 6
    context_insufficient_prompt: Annotated[
        LocaleString | LocaleInput | None,
        Field(
            description="Prompt fragment used when the guard rejects and the agent must communicate that it cannot answer.",
        ),
    ] = AgentLocaleString.from_i18n_path(
        "agent.context_sufficient_guard_step.config.context_insufficient_prompt.default"
    )

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            check_context_sufficiency=Checkbox(
                label=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.check_context_sufficiency.label"
                ),
                help=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.check_context_sufficiency.help"
                ),
                ref="check_context_sufficiency_enabled",
            ),
            max_hops=InputNumber(
                label=AgentLocaleString.from_i18n_path("agent.context_sufficient_guard_step.config.max_hops.label"),
                help=AgentLocaleString.from_i18n_path("agent.context_sufficient_guard_step.config.max_hops.help"),
                min=1,
                max=10,
                step=1,
                condition_if="$get(check_context_sufficiency_enabled).value",
            ),
            max_non_system_messages_in_guard=InputNumber(
                label=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.max_non_system_messages_in_guard.label"
                ),
                help=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.max_non_system_messages_in_guard.help"
                ),
                min=0,
                max=50,
                step=1,
                condition_if="$get(check_context_sufficiency_enabled).value",
            ),
            context_insufficient_prompt=LocaleString.as_form(
                label=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.context_insufficient_prompt.label"
                ),
                help_text=AgentLocaleString.from_i18n_path(
                    "agent.context_sufficient_guard_step.config.context_insufficient_prompt.help"
                ),
                input_type="textarea",
                condition_if="$get(check_context_sufficiency_enabled).value",
            ),
        )
