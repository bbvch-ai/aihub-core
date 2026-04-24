from typing import Annotated

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from pydantic import Field

from swiss_ai_hub.core.generative_ai.chat_history.format_chat_history import format_chat_history
from swiss_ai_hub.core.generative_ai.guards.guard_result import GuardResult
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler


class ContextGuardResult(GuardResult):
    """
    Specialized result for context sufficiency guards.

    Extends GuardResult with an additional field for new query suggestions
    when the current context is insufficient.
    """

    new_query: Annotated[
        str | None,
        Field(description="A revised query to get better search results if context was insufficient.", default=None),
    ]


def context_guard_result_factory(t: LocaleHandler, more_hops_available: bool) -> type[ContextGuardResult]:
    if more_hops_available:

        class LocalizedContextGuardResult(ContextGuardResult):
            reasoning: Annotated[str, Field(description=t("lib.guards.context_sufficient_guard.reason"))]
            success: Annotated[bool, Field(description=t("lib.guards.context_sufficient_guard.success"))]
            new_query: Annotated[str, Field(description=t("lib.guards.context_sufficient_guard.new_query"))]

        LocalizedContextGuardResult.__doc__ = t("lib.guards.context_sufficient_guard.docstring")
        return LocalizedContextGuardResult
    else:

        class LocalizedContextGuardResult(ContextGuardResult):
            reasoning: Annotated[str, Field(description=t("lib.guards.context_sufficient_guard.reason_no_hops"))]
            success: Annotated[bool, Field(description=t("lib.guards.context_sufficient_guard.success_no_hops"))]

        LocalizedContextGuardResult.__doc__ = t("lib.guards.context_sufficient_guard.docstring_no_hops")
        return LocalizedContextGuardResult


async def context_sufficient_guard(
    llm: LLM,
    t: LocaleHandler,
    user_query: str,
    context: str,
    prev_queries: list[str],
    more_hops_available: bool,
    chat_history: list[ChatMessage],
) -> ContextGuardResult:
    sufficiency_prompt = PromptTemplate(t("lib.guards.context_sufficient_guard.prompt"))
    if prev_queries:
        prev_queries = "\n".join(prev_queries)
    llm_kwargs: dict = {}
    if llm.metadata.is_function_calling_model:
        # Force the structured-output tool so the model can't fall back to plain text,
        # which breaks llama_index's structured_predict (ValueError: got 0 tool calls).
        # This matters especially when chat_history is long (e.g. retrieved memory).
        llm_kwargs["tool_choice"] = "required"
    else:
        llm_kwargs["tool_choice"] = NOT_GIVEN

    result = llm.structured_predict(
        context_guard_result_factory(t=t, more_hops_available=more_hops_available),
        sufficiency_prompt,
        llm_kwargs=llm_kwargs,
        user_query=user_query,
        context=context,
        prev_queries=prev_queries,
        chat_history=format_chat_history(chat_history),
    )

    guard_result = ContextGuardResult.model_validate(result)

    return guard_result
