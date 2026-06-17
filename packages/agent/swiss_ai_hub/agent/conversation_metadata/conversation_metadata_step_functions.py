import logging

from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.llms import LLM
from openai import NOT_GIVEN
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ConversationTagsEvent,
    ConversationTitleEvent,
    SuggestedFollowUpQuestionsEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.follow_up_questions_result import FollowUpQuestionsResult
from swiss_ai_hub.agent.conversation_metadata.tags_result import TagsResult
from swiss_ai_hub.agent.conversation_metadata.title_result import TitleResult

logger = logging.getLogger(__name__)

CONVERSATION_TITLE_KEY = "conversation_title"


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
) -> ConversationTitleEvent | None:
    """Generate a conversation title, or None when no topic is identifiable yet."""
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
        return None
    return ConversationTitleEvent(title=title)


async def do_generate_title_once(
    chat_messages: list[ChatMessage],
    thread_context: ThreadContext,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> ConversationTitleEvent | None:
    """Generate the conversation title only while none is stored, then freeze it for the thread.

    A thread keeps a single, stable title: once one is determined and stored in ThreadContext, later
    turns short-circuit without an LLM call. Until then, undeterminable turns (greetings, small talk)
    leave the title unset so a later turn can retry.
    """
    if await thread_context.get(CONVERSATION_TITLE_KEY):
        return None

    event = await do_generate_title(chat_messages, llm_config, displayer, t)
    if event is None:
        return None

    await thread_context.set(CONVERSATION_TITLE_KEY, event.title)
    return event


async def do_generate_tags(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> ConversationTagsEvent | None:
    """Generate category tags describing the conversation, or None when no topic is identifiable yet."""
    await displayer.display_thought(t("agent.conversation_metadata.thoughts.generating_tags"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        prompt = PromptTemplate(t("agent.conversation_metadata.prompts.tags"))
        result: TagsResult = await llm.astructured_predict(
            TagsResult,
            prompt,
            llm_kwargs=_structured_predict_kwargs(llm),
            conversation=_format_conversation(chat_messages),
        )

    tags = [tag.strip() for tag in result.tags if tag.strip()]
    if not tags:
        return None
    return ConversationTagsEvent(tags=tags)


async def do_suggest_follow_up_questions(
    chat_messages: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> SuggestedFollowUpQuestionsEvent | None:
    """Suggest follow-up questions for the latest answer, or None when none are appropriate."""
    await displayer.display_thought(t("agent.conversation_metadata.thoughts.suggesting_follow_ups"))

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
        return None
    return SuggestedFollowUpQuestionsEvent(questions=questions)
