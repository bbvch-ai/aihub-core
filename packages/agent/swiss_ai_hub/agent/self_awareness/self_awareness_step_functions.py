from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from openai import BadRequestError
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMStopEvent, MetaQuestionDetectedEvent, NotAMetaQuestionEvent
from swiss_ai_hub.core.generative_ai import LLMConfig, merge_consecutive_messages
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.self_awareness.meta_question_detector import (
    REASONING_DISABLED_EXTRA_BODY,
    detect_meta_question,
)


async def do_detect_meta_question(
    user_query: str,
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
    """Classify the user message and emit the routing event for the self-awareness branch."""
    await displayer.display_thought(t("agent.self_awareness.thought.detecting"))

    async with llm_config.cost_reporting_llm(displayer) as llm:
        classification = await detect_meta_question(llm=llm, t=t, user_query=user_query)

    if classification.is_meta_question and classification.category is not None:
        return MetaQuestionDetectedEvent(
            user_query=user_query,
            category=classification.category,
            reasoning=classification.reasoning,
        )
    return NotAMetaQuestionEvent(reasoning=classification.reasoning)


async def do_answer_meta_question(
    event: MetaQuestionDetectedEvent,
    agent_name: str,
    agent_description: str,
    workflow_summary: str,
    chat_history: list[ChatMessage],
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> LLMStopEvent:
    """Answer a meta question from the agent's own identity and workflow, then stop the run."""
    await displayer.display_thought(t("agent.self_awareness.thought.answering"))

    system_prompt = t("agent.self_awareness.answer.prompt").format(
        agent_name=agent_name,
        agent_description=agent_description,
        workflow=workflow_summary,
        category=event.category,
    )
    # Defense in depth: drop empty-content turns before prompting. Most providers reject an empty
    # assistant message with a 400. The blank-answer race that produced these is fixed at the source
    # (#1443 drains display-event streams before teardown); this is now a backstop against any empty
    # turn that still slips through (e.g. a cached conversation or a different chat client).
    non_empty_history = [message for message in chat_history if str(message.content or "").strip()]
    # System prompt must lead the message list: strict providers (e.g. Qwen3.5 on Infomaniak) reject
    # a 400 "System message must be at the beginning" when it follows the conversation turns.
    messages = merge_consecutive_messages(
        [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt), *non_empty_history]
    )

    async with llm_config.cost_reporting_llm(displayer) as llm:
        # A meta answer restates the agent's own identity and workflow from a fixed system prompt — no
        # chain-of-thought needed, so the model's reasoning is pure latency (≈16s vs ≈7s with it off on
        # Qwen3.5). display_llm_stream drives stream_chat without per-call kwargs, so bake the reasoning-off
        # flag onto this freshly-built instance; fall back to a plain stream for models that reject it (400
        # before any chunk is emitted, so the retry is safe).
        _disable_reasoning(llm)
        try:
            return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=True)
        except BadRequestError:
            _enable_reasoning(llm)
            return await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=True)


def _disable_reasoning(llm: LLM) -> None:
    """Merge the reasoning-off flag into the instance's per-request extra_body for the streaming path."""
    extra_body = {**llm.additional_kwargs.get("extra_body", {}), **REASONING_DISABLED_EXTRA_BODY}
    llm.additional_kwargs = {**llm.additional_kwargs, "extra_body": extra_body}


def _enable_reasoning(llm: LLM) -> None:
    """Drop the reasoning-off flag so a Mistral-tokenizer retry sends a plain request."""
    additional_kwargs = {key: value for key, value in llm.additional_kwargs.items() if key != "extra_body"}
    llm.additional_kwargs = additional_kwargs
