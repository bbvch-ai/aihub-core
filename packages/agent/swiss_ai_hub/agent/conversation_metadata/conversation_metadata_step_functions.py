import asyncio
import json
import logging
from collections.abc import Awaitable

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.prompts import RichPromptTemplate
from openinference.semconv.trace import OpenInferenceMimeTypeValues, OpenInferenceSpanKindValues, SpanAttributes
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, FollowUpQuestionsEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import get_tracer

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.follow_up_questions_result import FollowUpQuestionsResult
from swiss_ai_hub.agent.conversation_metadata.title_result import TitleResult

logger = logging.getLogger(__name__)

TITLE_GENERATED_KEY = "title_generated"


def _conversation_messages(chat_messages: list[ChatMessage]) -> list[ChatMessage]:
    """Keep only the real user/assistant exchange for metadata generation.

    ``chat_messages`` carries the full LLM input + output — system prompts, injected context/memory, and
    (for tool-using agents like McpReactAgent) tool-call and tool-result turns. Summarizing that
    technical noise produces wrong titles/follow-ups (e.g. a tool name as the topic), so we restrict to
    user/assistant turns with actual text content.
    """
    return [
        message
        for message in chat_messages
        if message.role in (MessageRole.USER, MessageRole.ASSISTANT) and str(message.content or "").strip()
    ]


async def do_generate_title(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    thread_context: ThreadContext,
) -> str | None:
    """Generate a stable conversation title once per thread and emit it as a display event.

    A thread keeps a single, stable title: this fires on the first check for a thread (the
    ``ThreadContext`` flag unset) and never again — even a greeting gets a title on that first check,
    never deferred to a later turn. Returns ``None`` only when this turn skipped generation entirely
    (flag already set); a genuine failure propagates to the best-effort wrapper instead, which leaves the
    flag unset so a later turn retries — that is a different concern (transient error) from "the model
    judged the topic unclear."
    """
    if await thread_context.get(TITLE_GENERATED_KEY):
        return None

    await displayer.display_thought(t("agent.conversation_metadata.thoughts.generating_title"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = RichPromptTemplate(t("agent.conversation_metadata.prompts.title"))
        result: TitleResult = await llm.astructured_predict(
            TitleResult,
            prompt,
            chat_history=_conversation_messages(chat_messages),
        )

    title = result.title.strip() or t("agent.conversation_metadata.default_title")

    await displayer.display_event(ConversationTitleEvent(title=title))
    await thread_context.set(TITLE_GENERATED_KEY, True)
    return title


async def do_generate_follow_up_questions(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> list[str]:
    """Generate follow-up questions grounded on the latest answer and emit them as a display event.

    Regenerated every turn since the suggestions depend on the most recent answer. Returns the emitted
    questions (empty when none) for observability.
    """
    await displayer.display_thought(t("agent.conversation_metadata.thoughts.generating_follow_ups"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = RichPromptTemplate(t("agent.conversation_metadata.prompts.follow_ups"))
        result: FollowUpQuestionsResult = await llm.astructured_predict(
            FollowUpQuestionsResult,
            prompt,
            chat_history=_conversation_messages(chat_messages),
        )

    questions = [question.strip() for question in result.questions if question.strip()]
    if not questions:
        return []

    await displayer.display_event(FollowUpQuestionsEvent(questions=questions))
    return questions


def _trace_input(chat_messages: list[ChatMessage]) -> str:
    """Serialize the user/assistant turns actually fed to the generator, for the span's input."""
    turns = [
        {"role": message.role.value, "content": str(message.content or "")}
        for message in _conversation_messages(chat_messages)
    ]
    return json.dumps(turns, ensure_ascii=False)


async def _run_best_effort(span_name: str, input_value: str, coroutine: Awaitable[object]) -> None:
    """Run a metadata generator inside its own trace span, logging and swallowing any failure.

    Conversation metadata is a non-essential post-answer enhancement: a title/follow-up failure must
    degrade to "no metadata this turn" and never surface as an error or an ``ExceptionEvent`` on the run.
    Logged at WARNING (not ERROR) so an expected best-effort miss does not trip production error alerting.

    The span gives each generation a named Langfuse observation with the conversation it saw (input) and
    the title/questions it produced (output) — plus latency, cost, and a visible error-marked span on
    failure — even when the generator runs inline in a terminal step rather than as its own ``@step``.
    """
    with get_tracer(__name__).start_as_current_span(span_name) as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, OpenInferenceSpanKindValues.CHAIN.value)
        span.set_attribute(SpanAttributes.INPUT_VALUE, input_value)
        span.set_attribute(SpanAttributes.INPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value)
        try:
            output = await coroutine
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(output, ensure_ascii=False))
            span.set_attribute(SpanAttributes.OUTPUT_MIME_TYPE, OpenInferenceMimeTypeValues.JSON.value)
        except Exception as failure:
            span.set_attribute("operation.success", False)
            span.record_exception(failure)
            logger.warning("Conversation metadata generation failed (%s): %s", span_name, failure, exc_info=failure)


async def generate_title(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    thread_context: ThreadContext,
) -> None:
    """Best-effort title generation — never propagates (see ``_run_best_effort``).

    Anchored by RAGAgent/ExpertRAGAgent on an early, pre-answer event so it runs concurrently with the
    answer pipeline and emits before the stop event; the title only needs the conversation topic, not the
    answer.
    """
    await _run_best_effort(
        "generate_title",
        _trace_input(chat_messages),
        do_generate_title(chat_messages, llm_config, displayer, t, thread_context),
    )


async def generate_follow_up_questions(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> None:
    """Best-effort follow-up question generation — never propagates (see ``_run_best_effort``).

    Grounded on the latest answer, so it can only run once the answer exists — inline in the terminal
    step, before the stop event is returned.
    """
    await _run_best_effort(
        "generate_follow_up_questions",
        _trace_input(chat_messages),
        do_generate_follow_up_questions(chat_messages, llm_config, displayer, t),
    )


async def generate_conversation_metadata(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
    thread_context: ThreadContext,
) -> None:
    """Generate title + follow-up questions inline, best-effort, for agents whose answer is a stop event.

    Conversation metadata is a non-essential, post-answer enhancement. Agents whose answer is a terminal
    stop event (``LLMWrappingAgent``, ``FewShotAgent``, ``McpReactAgent``) cannot adopt it as a separate
    ``@step``: ``AgentDispatcher.handle_event`` cleans up and returns on a stop event **before** it
    dispatches steps waiting on that event, so such a step would never run. Calling the generators here —
    inside the terminal step, before it returns the stop event — emits the display events while the step
    body runs, i.e. on the wire **before** the stop event is published and before teardown. (See ADR
    ``2026_06_18_conversation_metadata_as_explicit_per_agent_steps``.)

    Both generators are best-effort, so a failure in either is logged and swallowed and the run still
    terminates normally with its answer intact.
    """
    await asyncio.gather(
        generate_title(chat_messages, llm_config, displayer, t, thread_context),
        generate_follow_up_questions(chat_messages, llm_config, displayer, t),
    )
