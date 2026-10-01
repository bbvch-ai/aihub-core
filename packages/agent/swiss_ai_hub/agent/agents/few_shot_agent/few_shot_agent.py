from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentSuitabilityAcceptEvent,
    AgentSuitabilityRejectEvent,
    LLMEvent,
    MemoryStorageRequestedEvent,
    Message,
    RefusalReason,
    RefusalStopEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    agent_description_guard,
    create_few_shot_messages,
    estimate_prompt_tokens,
    limit_chat_history,
    merge_consecutive_messages,
    usable_input_budget,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.few_shot_agent.events.few_shot_event import FewShotEvent
from swiss_ai_hub.agent.agents.few_shot_agent.few_shot_agent_config import FewShotAgentConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class FewShotAgent(Agent):
    """
    Implements a Few Shot Agent.

    The blueprint guards the request against its own description, then answers from its few-shot examples
    and the turn's query rather than from the conversation itself. It hands the conversation to the
    conversation capability and asks the memory capability for what it remembers; the memories join the
    prompt as system messages next to the client's, since the examples stand in for the history.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.few_shot_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.few_shot_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:book"
    completion_stops: ClassVar[tuple[type[StopEvent], ...]] = (RefusalStopEvent,)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> Conversation.ContextualizeRequest | RefusalStopEvent:
        """Truncate the chat history to the token limit, and refuse the run when it still cannot be sent.

        Truncation alone cannot bound the prompt: `ChatMemoryBuffer.get` falls through to `chat_history[-1:]` when a
        single message exceeds the limit, and OpenWebUI under `RAG_FULL_CONTEXT` pastes a whole uploaded file into the
        chat. The suitability guard and the condenser send that text to the task model, whose 400 would otherwise
        surface as an error banner instead of an answer.

        Client system messages are irreducible alongside the last turn: every step forwards them, and OpenWebUI can
        place file text there too.
        """
        budget = usable_input_budget([agent_config.llm, agent_config.task_llm])
        if budget is None:
            limited = limit_chat_history(
                chat_history=event.messages, number_of_input_tokens=agent_config.number_of_input_tokens
            )
            return Conversation.contextualize(history=limited, message=event)

        system_messages = [msg for msg in event.messages if msg.role == MessageRole.SYSTEM]
        conversation = [msg for msg in event.messages if msg.role != MessageRole.SYSTEM]
        irreducible = [*system_messages, *conversation[-1:]]
        irreducible_tokens = estimate_prompt_tokens(irreducible, agent_config.llm.token_counter)
        if irreducible_tokens > budget:
            return await self._refuse_oversized_input(irreducible_tokens, budget, agent_config, displayer, t)

        # Trim only what precedes the last turn: handing the trimmer a list that still holds it charges it twice, and
        # `ChatMemoryBuffer` then drops the whole earlier conversation.
        older_limit = min(agent_config.number_of_input_tokens, budget - irreducible_tokens)
        older = (
            limit_chat_history(chat_history=conversation[:-1], number_of_input_tokens=older_limit)
            if older_limit > 0
            else []
        )
        return Conversation.contextualize(history=[*system_messages, *older, *conversation[-1:]], message=event)

    @staticmethod
    async def _refuse_oversized_input(
        needed: int,
        budget: int,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RefusalStopEvent:
        """Stop the run with a reply rather than an error, keeping the token arithmetic to the thought.

        The wording differs from the other blueprints on purpose: this agent answers from its examples and a condensed
        question, never from the document itself, so advising a smaller file would promise something it cannot do.
        """
        await displayer.display_thought(
            t("agent.few_shot_agent.thoughts.input_too_large", tokens=needed, budget=budget)
        )
        refusal = t("agent.few_shot_agent.messages.input_too_large")
        model_name = agent_config.llm.model_name
        await displayer.display_chunk(refusal, model_name=model_name)
        return RefusalStopEvent(
            reason=RefusalReason.INPUT_TOO_LARGE,
            output_messages=[Message.from_string(role="assistant", content=refusal, name=model_name)],
            chat_model_name=model_name,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.recall_memory.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.recall_memory.description"),
        icon="mdi:brain",
    )
    async def recall_memory_step(self, ctx: Conversation.Contextualized) -> Memory.RecallRequest:
        return Memory.recall(ctx.query)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.agent_suitability_guard.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.agent_suitability_guard.description"),
        icon="mage:shield-check",
    )
    async def right_agent_guard(
        self,
        ctx: Conversation.Contextualized,
        start_event: UserMessageEvent,
        t: LocaleHandler,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        user: UserIdentity | None = None,
    ) -> AgentSuitabilityAcceptEvent | AgentSuitabilityRejectEvent:
        """Judges the raw request once the conversation has cleared it."""
        async with agent_config.task_llm.cost_reporting_llm(displayer, user=user) as llm:
            guard_result = await agent_description_guard(
                agent_description=agent_config.description,
                llm=llm,
                t=t,
                user_query=start_event.user_query,
                messages=ctx.history,
            )
        if not guard_result.success:
            return AgentSuitabilityRejectEvent(reason=guard_result.reasoning)
        return AgentSuitabilityAcceptEvent(
            reason=guard_result.reasoning,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.create_few_shot_examples.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.create_few_shot_examples.description"),
        icon="mage:checklist",
    )
    async def create_few_shot_examples(
        self,
        ctx: Conversation.Contextualized,
        _: AgentSuitabilityAcceptEvent,
        memories: Memory.Recalled,
        start_event: UserMessageEvent,
        agent_config: FewShotAgentConfig,
    ) -> FewShotEvent:
        """
        Creates the few-shot examples from the configuration and the context for the LLM call: the client's
        system messages, the agent's own system prompt, the recalled memories, the examples and the turn's query.
        Important: the conversation turns are not used directly (only through the query), as the few-shot
        examples are used instead. Same applies to the original user message.
        """
        locale = start_event.locale
        few_shot_messages = create_few_shot_messages(agent_config.few_shot.few_shot_examples, locale)
        system_messages = [msg for msg in ctx.history if msg.role == MessageRole.SYSTEM]
        system_prompt = ChatMessage(
            role=MessageRole.SYSTEM, content=agent_config.few_shot.system_prompt.in_locale(locale)
        )
        # Only one leading system message may survive: strict providers (e.g. Qwen3.5 on Infomaniak) reject a
        # 400 "System message must be at the beginning" for any system message past index 0, and the chat
        # client's own system prompt (OpenWebUI model prompt, bot PathEntity.system_message) would push ours
        # to index 1.
        context = merge_consecutive_messages(
            [
                *system_messages,
                system_prompt,
                *[message for block in memories.blocks for message in block],
                *few_shot_messages,
                ChatMessage(role=MessageRole.USER, content=ctx.query),
            ]
        )
        return FewShotEvent(
            few_shot_examples=few_shot_messages,
            system_prompt=system_prompt,
            full_context=context,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.respond_with_llm.name"),
        description=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.respond_with_llm.description"),
        icon="mage:message",
    )
    async def respond_with_llm_step(
        self,
        event: FewShotEvent,
        ctx: Conversation.Contextualized,
        agent_config: FewShotAgentConfig,
        displayer: EventDisplayer,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """Stream the answer, then hand the turn back: the memory delegation first, the completion last."""
        await displayer.display_thought(t("agent.thought.write_answer_based_on_few_shot_examples"))
        async with agent_config.llm.cost_reporting_llm(displayer, user=user) as llm:
            answer = await displayer.display_llm_stream(agent_config.llm, llm, event.full_context, as_stop_step=False)
        remember = Memory.remember(
            query=ctx.query,
            answer=answer,
            user=user,
            topic=topic,
            agent_config=agent_config,
            memory=agent_config,
            locale=t.locale,
        )
        return [*([remember] if remember else []), Conversation.complete(answer=answer)]

    @step(
        name=AgentLocaleString.from_i18n_path("agent.few_shot_agent.steps.reject_unsuitable_request.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.few_shot_agent.steps.reject_unsuitable_request.description"
        ),
        icon="mage:cancel",
    )
    async def reject_unsuitable_request_step(
        self,
        event: AgentSuitabilityRejectEvent,
        ctx: Conversation.Contextualized,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> Conversation.CompleteRequest:
        """End a rejected request with a streamed refusal, since a bare stop event reaches chat clients as an
        empty message.

        The guard's `reason` carries the specific mismatch in the run's locale, but it is third-person
        justification, so a first-person sentence leads it. The completion grounds the follow-ups on the
        refusal the user actually read.
        """
        refusal = t("agent.few_shot_agent.messages.unsuitable_request", reason=event.reason)
        await displayer.display_chunk(refusal, model_name=FewShotAgent.__name__)
        output_messages = [Message.from_string(role="assistant", content=refusal, name=FewShotAgent.__name__)]
        answer = LLMEvent(
            input_messages=[Message.from_llama_index(message) for message in ctx.history],
            output_messages=output_messages,
        )
        stop = RefusalStopEvent(
            reason=RefusalReason.OUT_OF_SCOPE, output_messages=output_messages, chat_model_name=FewShotAgent.__name__
        )
        return Conversation.complete(answer=answer, stop=stop)
