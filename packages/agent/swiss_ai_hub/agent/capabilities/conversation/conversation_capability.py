from collections.abc import Callable
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AnswerPostProcessedEvent,
    ContextBlockEvent,
    ConversationQueryEvent,
    EnrichedChatHistoryEvent,
    LimitChatHistoryEvent,
    LLMEvent,
    LLMStopEvent,
    Message,
    NotAMetaQuestionEvent,
    RefusalReason,
    RefusalStopEvent,
    StandaloneQuestionCondenserEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    EmptyCondensationError,
    LLMConfig,
    condense_standalone_question,
    estimate_prompt_tokens,
    limit_chat_history,
    usable_input_budget,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.conversation.conversation_preconditions import (
    all_context_blocks_reported,
    all_post_answer_hooks_reported,
    passed_meta_question_gate,
)
from swiss_ai_hub.agent.capabilities.conversation.conversation_wiring import ConversationWiring
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.conversation_metadata.conversation_metadata_step_functions import (
    generate_follow_up_questions,
    generate_title,
)
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class ConversationCapability(Capability):
    """
    The spine every chat blueprint shares, from the limited history to the stop event.

    A blueprint supplies the entry step that turns its start event into a `LimitChatHistoryEvent`, and the
    answer pipeline that turns the `EnrichedChatHistoryEvent` into an `LLMEvent`. The spine does the rest:
    it holds the turn at the meta-question gate, derives the one query enrichers and retrieval share,
    joins every enricher's context block into the history, titles the thread, and stops the run once each
    post-answer hook has reported.

    Two steps are defaults the spine withholds when the blueprint already provides them: the gate opener,
    replaced by `SelfAwarenessCapability`'s detection, and the stop, replaced by a blueprint whose stop
    event carries more than the answer.
    """

    required_config: ClassVar[type[ConversationFields]] = ConversationFields

    @classmethod
    def steps_for(cls, blueprint: type[Agent]) -> list[Callable]:
        defaults = {cls.open_gate_step, cls.stop_step}
        steps = [step for step in cls.own_steps() if step not in defaults]
        siblings = [
            step for capability in blueprint.capabilities if capability is not cls for step in capability.own_steps()
        ]
        provided = [*blueprint.get_own_steps(), *siblings]
        if NotAMetaQuestionEvent not in Capability.produced_events(provided):
            steps.append(cls.open_gate_step)
        if not ConversationWiring.stops_after_answer(provided):
            steps.append(cls.stop_step)
        return steps

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.open_gate.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.open_gate.description"),
        icon="mdi:door-open",
    )
    async def open_gate_step(agent: Agent, event: UserMessageEvent) -> NotAMetaQuestionEvent:
        """Release every chat message at once on a blueprint without meta-question detection."""
        return NotAMetaQuestionEvent(reasoning="This assistant does not detect meta questions.")

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.derive_query.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.derive_query.description"),
        icon="mage:archive",
        precondition=passed_meta_question_gate,
    )
    async def derive_query_step(
        agent: Agent,
        history: LimitChatHistoryEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        user_message: UserMessageEvent | None = None,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> list[ConversationQueryEvent | StandaloneQuestionCondenserEvent] | RefusalStopEvent:
        """The turn's query: the last user message as is, or condensed out of the history on request.

        Held at the meta-question gate on purpose: this is the first step past the entry point, so gating it
        here gates every enricher and the whole answer pipeline behind detection at once.
        """
        last_user_message = history.limited_history[-1]
        if not conversation.condense_question:
            return [ConversationQueryEvent(query=last_user_message.content or "")]

        await displayer.display_thought(t("agent.thought.condense_question"))
        async with conversation.task_llm.cost_reporting_llm(displayer, user=user) as llm:
            try:
                condensed = await condense_standalone_question(
                    chat_history=history.limited_history, message=last_user_message, t=t, llm=llm
                )
            except EmptyCondensationError:
                return await _refuse_empty_condensation(conversation.task_llm, displayer, t)
        return [
            StandaloneQuestionCondenserEvent(condensed_chat_message=condensed),
            ConversationQueryEvent(query=(condensed.content or "").strip(), condensed=True),
        ]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_context.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_context.description"),
        icon="mdi:database-plus",
        precondition=all_context_blocks_reported,
    )
    async def assemble_context_step(
        agent: Agent,
        history: LimitChatHistoryEvent,
        conversation: ConversationFields,
        blocks: list[ContextBlockEvent] | None = None,
    ) -> EnrichedChatHistoryEvent:
        """Merge every enricher's block into the history, behind the leading system messages, within budget.

        Re-limited before it leaves this step so `extended_history` carries the same "fits the budget"
        guarantee `LimitChatHistoryEvent.limited_history` does. The blocks sit at the front of the trimmed
        part, so they are what gives way when the result does not fit — never the turn the user asked about,
        and never the system head, which is held out of the trim altogether.
        """
        system_head, turns = _split_system_head(history.limited_history)
        block_messages = [
            message for block in sorted(blocks or [], key=lambda block: block.source) for message in block.messages
        ]
        if not block_messages:
            return EnrichedChatHistoryEvent(extended_history=history.limited_history)

        budget = _input_budget(conversation) - estimate_prompt_tokens(system_head, conversation.llm.token_counter)
        limited = limit_chat_history(
            chat_history=[*block_messages, *turns],
            number_of_input_tokens=max(budget, 1),
        )
        return EnrichedChatHistoryEvent(extended_history=[*system_head, *limited])

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation_metadata.steps.title.description"),
        icon="mdi:format-title",
        stop_on_error=False,
    )
    async def generate_conversation_title_step(
        agent: Agent,
        _query: ConversationQueryEvent,
        history: LimitChatHistoryEvent,
        conversation: ConversationFields,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> None:
        """Title the thread concurrently with the answer pipeline, anchored just past the gate.

        The query event is the trigger because it is the first event a meta question never produces; the
        history is what the title is made from.
        """
        await generate_title(
            chat_messages=history.limited_history,
            llm_config=conversation.task_llm,
            displayer=displayer,
            t=t,
            thread_context=thread_context,
            user=user,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.stop.description"),
        precondition=all_post_answer_hooks_reported,
    )
    async def stop_step(
        agent: Agent,
        llm_event: LLMEvent,
        conversation: ConversationFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None = None,
        _hooks: list[AnswerPostProcessedEvent] | None = None,
    ) -> LLMStopEvent:
        """Turn the answer into the stop event once every post-answer hook has reported.

        Follow-up questions are generated inline here: they are grounded on the answer, so they cannot start
        earlier, and emitting them before the stop event puts them on the wire ahead of teardown.
        """
        await generate_follow_up_questions(llm_event.chat_messages, conversation.task_llm, displayer, t, user)
        return LLMStopEvent.model_validate(llm_event.model_dump(exclude={"event_id", "created_at"}))


def _split_system_head(messages: list[ChatMessage]) -> tuple[list[ChatMessage], list[ChatMessage]]:
    head_length = 0
    for message in messages:
        if message.role != MessageRole.SYSTEM:
            break
        head_length += 1
    return messages[:head_length], messages[head_length:]


def _input_budget(conversation: ConversationFields) -> int:
    """The admin's cost ceiling capped by the narrowest model window that could receive the prompt."""
    budget = usable_input_budget([conversation.llm, conversation.task_llm])
    return conversation.number_of_input_tokens if budget is None else min(conversation.number_of_input_tokens, budget)


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
