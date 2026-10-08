from collections.abc import Callable, Sequence
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    CompleteConversationEvent,
    ComposeContextEvent,
    ContextComposedEvent,
    ContextualizeConversationEvent,
    ConversationContextualizedEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    RefusalReason,
    RefusalStopEvent,
    StandaloneQuestionCondenserEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    EmptyCondensationError,
    LLMConfig,
    condense_standalone_question,
    estimate_prompt_tokens,
    limit_chat_history,
    merge_consecutive_messages,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    generate_follow_up_questions,
    generate_title,
)
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import summarize_workflow_for_meta_answer
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)
from swiss_ai_hub.agent.workflow.decorators.step import step

_ROLES_THAT_CANNOT_LEAD = (MessageRole.ASSISTANT, MessageRole.TOOL)


class Conversation(Capability):
    """
    What every chat blueprint hands over to a capability rather than writing itself, as three calls:

    - `contextualize(history, message)` inspects the message for a meta question and answers it if it is one,
      derives the query the turn is answered for, and titles the thread. Answered with
      `ConversationContextualizedEvent`, or with a stop event when the turn ended in there.
    - `compose(history, blocks)` merges context blocks into the history, in the given order, within the input
      budget. Answered with `ContextComposedEvent`, which the chat displays as what the model saw.
    - `complete(answer, stop)` generates the follow-up questions and ends the run with the given stop event, or
      an `LLMStopEvent` carrying the answer.

    The meta-question gate lives inside `contextualize` on purpose: a blueprint that had to gate its own steps
    could forget to, and detection would race its pipeline. Here nothing downstream exists until the message
    is cleared.
    """

    calls: ClassVar[dict] = {
        ContextualizeConversationEvent: (ConversationContextualizedEvent, LLMStopEvent, RefusalStopEvent),
        ComposeContextEvent: (ContextComposedEvent,),
        CompleteConversationEvent: (StopEvent,),
    }
    required_config: ClassVar[type[ConversationFields]] = ConversationFields

    ContextualizeRequest = ContextualizeConversationEvent
    Contextualized = ConversationContextualizedEvent
    ComposeRequest = ComposeContextEvent
    Composed = ContextComposedEvent
    CompleteRequest = CompleteConversationEvent

    @staticmethod
    def contextualize(
        history: list[ChatMessage], message: UserMessageEvent | None = None
    ) -> ContextualizeConversationEvent:
        """Hand the limited history over; pass the user's message so it is inspected for a meta question."""
        if message is None:
            return ContextualizeConversationEvent(history=history)
        return ContextualizeConversationEvent(
            history=history, user_query=message.user_query, attached_file_names=message.attached_file_names
        )

    @staticmethod
    def compose(history: list[ChatMessage], blocks: Sequence[list[ChatMessage]]) -> ComposeContextEvent:
        """Ask for the history with these blocks merged in, in this order."""
        return ComposeContextEvent(history=history, blocks=list(blocks))

    @staticmethod
    def complete(answer: LLMEvent, stop: StopEvent | None = None) -> CompleteConversationEvent:
        """End the turn on this answer; return it last from a step, behind anything that must be published first."""
        return CompleteConversationEvent(answer=answer, stop=stop)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def inspect_message_step(
        agent: Agent,
        request: ContextualizeConversationEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Classify the message as a meta question or clear it; a programmatic start has no message to inspect."""
        if request.user_query is None:
            return NotAMetaQuestionEvent(reasoning="Programmatic start: no user message to inspect.")
        return await do_detect_meta_question(
            user_query=request.user_query,
            attached_file_names=request.attached_file_names,
            llm_config=conversation.task_llm,
            displayer=displayer,
            user=user,
            t=t,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        agent: Agent,
        event: MetaQuestionDetectedEvent,
        request: ContextualizeConversationEvent,
        agent_config: AgentConfig,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> LLMStopEvent:
        """Answer a meta question from the blueprint's own identity and workflow, then stop the run.

        Follow-ups only: the title runs in parallel via `generate_meta_question_title_step`, since it needs
        the topic, not the answer.
        """
        stop_event = await do_answer_meta_question(
            event=event,
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            workflow_summary=summarize_workflow_for_meta_answer(type(agent), t),
            chat_history=request.history,
            llm_config=conversation.task_llm,
            displayer=displayer,
            user=user,
            t=t,
        )
        await generate_follow_up_questions(stop_event.chat_messages, conversation.task_llm, displayer, t, user)
        return stop_event

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.description"),
        icon="mdi:format-title",
        stop_on_error=False,
    )
    async def generate_meta_question_title_step(
        agent: Agent,
        event: MetaQuestionDetectedEvent,
        request: ContextualizeConversationEvent,
        conversation: ConversationFields,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> None:
        """Title the thread in parallel with the meta answer, which it must not wait for."""
        await generate_title(
            chat_messages=request.history,
            llm_config=conversation.task_llm,
            displayer=displayer,
            t=t,
            thread_context=thread_context,
            user=user,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.derive_query.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.derive_query.description"),
        icon="mage:archive",
    )
    async def derive_query_step(
        agent: Agent,
        request: ContextualizeConversationEvent,
        _cleared: NotAMetaQuestionEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[ConversationContextualizedEvent | StandaloneQuestionCondenserEvent] | RefusalStopEvent:
        """The turn's query, once the message is cleared: the last user message as is, or condensed on request."""
        last_user_message = request.history[-1]
        if not conversation.condense_question:
            return [ConversationContextualizedEvent(history=request.history, query=last_user_message.content or "")]

        await displayer.display_thought(t("agent.thought.condense_question"))
        async with conversation.task_llm.cost_reporting_llm(displayer, user=user) as llm:
            try:
                condensed = await condense_standalone_question(
                    chat_history=request.history, message=last_user_message, t=t, llm=llm
                )
            except EmptyCondensationError:
                return await _refuse_empty_condensation(conversation.task_llm, displayer, t)
        return [
            StandaloneQuestionCondenserEvent(condensed_chat_message=condensed),
            ConversationContextualizedEvent(
                history=request.history, query=(condensed.content or "").strip(), condensed=True
            ),
        ]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.description"),
        icon="mdi:format-title",
        stop_on_error=False,
    )
    async def generate_conversation_title_step(
        agent: Agent,
        event: ConversationContextualizedEvent,
        conversation: ConversationFields,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> None:
        """Title the thread concurrently with the answer pipeline; the query event is the first past the gate."""
        await generate_title(
            chat_messages=event.history,
            llm_config=conversation.task_llm,
            displayer=displayer,
            t=t,
            thread_context=thread_context,
            user=user,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.compose_context.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.compose_context.description"),
        icon="mdi:database-plus",
    )
    async def compose_context_step(
        agent: Agent,
        request: ComposeContextEvent,
        conversation: ConversationFields,
    ) -> ContextComposedEvent:
        """Merge the blocks behind the leading system messages, within budget, as `Conversation.fit` does."""
        return ContextComposedEvent(history=Conversation.fit(request.history, request.blocks, conversation))

    @staticmethod
    def fit(
        history: list[ChatMessage], blocks: Sequence[list[ChatMessage]], conversation: ConversationFields
    ) -> list[ChatMessage]:
        """The history with the blocks merged behind its leading system messages, re-limited to the input budget.

        Every part is measured with the model's own count, so the result keeps the "fits the budget" guarantee
        the limited history carries, also when the caller added instructions to it. Consecutive messages of one
        role leave merged, as the model receives them: served models (Gemma behind vLLM) lose context spread
        over several system messages, and strict chat templates (Qwen) reject a system message anywhere else.
        What gives way when the result does not fit is the oldest turns first, since the blocks were asked for
        this turn; then whole blocks from the front, never part of one, and never the question or the system head.
        """
        counter = conversation.llm.token_counter
        system_head, turns = _split_system_head(history)
        earlier, question = turns[:-1], turns[-1:]
        room = conversation.input_budget() - estimate_prompt_tokens([*system_head, *question], counter)
        fitted_blocks = _fit_whole_blocks(blocks, room, counter)
        kept = _fit_newest_turns(earlier, room - estimate_prompt_tokens(fitted_blocks, counter), counter)
        return merge_consecutive_messages([*system_head, *fitted_blocks, *kept, *question])

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.complete.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.complete.description"),
        icon="mage:stop-circle-fill",
    )
    async def complete_conversation_step(
        agent: Agent,
        request: CompleteConversationEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> StopEvent:
        """Generate the follow-up questions from the answer, then end the run.

        Follow-ups are grounded on the answer, so they cannot start earlier, and emitting them before the stop
        event puts them on the wire ahead of teardown.
        """
        await generate_follow_up_questions(request.answer.chat_messages, conversation.task_llm, displayer, t, user)
        if request.stop is not None:
            return request.stop
        return LLMStopEvent.model_validate(request.answer.model_dump(exclude={"event_id", "created_at"}))


def _split_system_head(messages: list[ChatMessage]) -> tuple[list[ChatMessage], list[ChatMessage]]:
    head_length = 0
    for message in messages:
        if message.role != MessageRole.SYSTEM:
            break
        head_length += 1
    return messages[:head_length], messages[head_length:]


def _fit_whole_blocks(
    blocks: Sequence[list[ChatMessage]], room: int, counter: Callable[[str], list[int]]
) -> list[ChatMessage]:
    """The blocks that fit `room`, the last first. A block goes in whole or not at all: an attached-file block cut in
    part would keep its citation rule and notes without the content they describe."""
    kept: list[list[ChatMessage]] = []
    for block in reversed(blocks):
        cost = estimate_prompt_tokens(block, counter)
        if block and cost <= room:
            kept.insert(0, block)
            room -= cost
    return [message for block in kept for message in block]


def _fit_newest_turns(turns: list[ChatMessage], room: int, counter: Callable[[str], list[int]]) -> list[ChatMessage]:
    """The newest turns that fit `room` by the model's own count. `limit_chat_history` counts with another tokenizer
    and keeps its newest message even when that alone is too long, so its result is cut again here."""
    if room <= 0:
        return []
    kept = limit_chat_history(chat_history=turns, number_of_input_tokens=room)
    costs = [estimate_prompt_tokens([message], counter) for message in kept]
    total, start = sum(costs), 0
    while total > room and start < len(kept):
        total -= costs[start]
        start += 1
        while start < len(kept) and kept[start].role in _ROLES_THAT_CANNOT_LEAD:
            total -= costs[start]
            start += 1
    return kept[start:]


async def _refuse_empty_condensation(
    llm_config: LLMConfig,
    displayer: EventDisplayer,
    t: LocaleHandler,
) -> RefusalStopEvent:
    """Stop the run with a message the user can act on, keeping the mechanism to the thought.

    Retrying is pointless (an identical re-issue returns the same nothing) and there is no fallback question
    to answer with, so asking the user to rephrase is the only useful move left.
    """
    await displayer.display_thought(t("agent.conversation.thoughts.condensation_empty"))
    refusal = t("agent.conversation.messages.condensation_empty")
    await displayer.display_chunk(refusal, model_name=llm_config.model_name)
    return RefusalStopEvent(
        reason=RefusalReason.CONDENSATION_EMPTY,
        output_messages=[Message.from_string(role="assistant", content=refusal, name=llm_config.model_name)],
        chat_model_name=llm_config.model_name,
    )
