import logging

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
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


def _format_conversation(chat_messages: list[ChatMessage]) -> str:
    """Render the conversation as a plain transcript for the metadata prompts."""
    lines = [
        f"{message.role.value}: {content}"
        for message in chat_messages
        if (content := str(message.content or "").strip())
    ]
    return "\n".join(lines)


def _structured_predict_kwargs(llm: LLM) -> dict:
    """Force tool use on function-calling models so structured output stays reliable."""
    return {"tool_choice": "required" if llm.metadata.is_function_calling_model else NOT_GIVEN}


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
        prompt = PromptTemplate(t("agent.conversation_metadata.prompts.title"))
        result: TitleResult = await llm.astructured_predict(
            TitleResult,
            prompt,
            llm_kwargs=_structured_predict_kwargs(llm),
            conversation=_format_conversation(chat_messages),
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
        prompt = PromptTemplate(t("agent.conversation_metadata.prompts.follow_ups"))
        result: FollowUpQuestionsResult = await llm.astructured_predict(
            FollowUpQuestionsResult,
            prompt,
            llm_kwargs=_structured_predict_kwargs(llm),
            conversation=_format_conversation(chat_messages),
        )

    questions = [question.strip() for question in result.questions if question.strip()]
    if not questions:
        return

    await displayer.display_event(FollowUpQuestionsEvent(questions=questions))
