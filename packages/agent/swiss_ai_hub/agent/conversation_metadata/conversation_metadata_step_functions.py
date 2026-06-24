import asyncio
import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.core.prompts import RichPromptTemplate
from openai import NOT_GIVEN
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ConversationTitleEvent, FollowUpQuestionsEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.follow_up_questions_result import FollowUpQuestionsResult
from swiss_ai_hub.agent.conversation_metadata.title_result import TitleResult

logger = logging.getLogger(__name__)

TITLE_GENERATED_KEY = "title_generated"


def _structured_predict_kwargs(llm: LLM) -> dict:
    """Force tool use on function-calling models so structured output stays reliable."""
    return {"tool_choice": "required" if llm.metadata.is_function_calling_model else NOT_GIVEN}


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
) -> None:
    """Generate a stable conversation title once per thread and emit it as a display event.

    A thread keeps a single, stable title: once one is generated and the ThreadContext flag is set,
    later turns short-circuit without an LLM call. Until then, undeterminable turns (greetings, small
    talk) leave the flag unset so a later turn can retry.
    """
    if await thread_context.get(TITLE_GENERATED_KEY):
        return

    await displayer.display_thought(t("agent.conversation_metadata.thoughts.generating_title"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = RichPromptTemplate(t("agent.conversation_metadata.prompts.title"))
        result: TitleResult = await llm.astructured_predict(
            TitleResult,
            prompt,
            llm_kwargs=_structured_predict_kwargs(llm),
            chat_history=_conversation_messages(chat_messages),
        )

    title = (result.title or "").strip()
    if not title:
        return

    await displayer.display_event(ConversationTitleEvent(title=title))
    await thread_context.set(TITLE_GENERATED_KEY, True)


async def do_generate_follow_up_questions(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> None:
    """Generate follow-up questions grounded on the latest answer and emit them as a display event.

    Regenerated every turn since the suggestions depend on the most recent answer.
    """
    await displayer.display_thought(t("agent.conversation_metadata.thoughts.generating_follow_ups"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = RichPromptTemplate(t("agent.conversation_metadata.prompts.follow_ups"))
        result: FollowUpQuestionsResult = await llm.astructured_predict(
            FollowUpQuestionsResult,
            prompt,
            llm_kwargs=_structured_predict_kwargs(llm),
            chat_history=_conversation_messages(chat_messages),
        )

    questions = [question.strip() for question in result.questions if question.strip()]
    if not questions:
        return

    await displayer.display_event(FollowUpQuestionsEvent(questions=questions))


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

    Running both generators with ``asyncio.gather(return_exceptions=True)`` keeps a failure in either from
    propagating: it is logged and the run still terminates normally with its answer intact.
    """
    results = await asyncio.gather(
        do_generate_title(chat_messages, llm_config, displayer, t, thread_context),
        do_generate_follow_up_questions(chat_messages, llm_config, displayer, t),
        return_exceptions=True,
    )
    for result in results:
        if isinstance(result, Exception):
            logger.warning("Conversation metadata generation failed: %s", result, exc_info=result)
