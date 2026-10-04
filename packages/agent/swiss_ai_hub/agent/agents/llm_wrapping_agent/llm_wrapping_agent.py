from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MemoryStorageRequestedEvent,
    RefusalStopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import (
    estimate_prompt_tokens,
    limit_chat_history,
    merge_consecutive_messages,
    usable_input_budget,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.conversation.oversized_input_refusal import OversizedInputRefusal
from swiss_ai_hub.agent.capabilities.knowledge.knowledge import Knowledge
from swiss_ai_hub.agent.capabilities.knowledge.knowledge_fields import KnowledgeFields
from swiss_ai_hub.agent.capabilities.memory.memory import Memory
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class LLMWrappingAgent(Agent):
    """A simple agent that wraps an LLM and streams responses to user messages.

    Four steps of its own: limit the history and hand it to the conversation, ask memory for what it knows,
    ask for the prompt with the memories merged in, and answer. The meta-question gate, the query, the title,
    the follow-ups and the stop are the conversation capability's; the memories are the memory capability's.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.llm_wrapping_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:message"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.name"),
        description=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.limit_chat_history.description"),
        icon="mage:edit",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> Conversation.ContextualizeRequest | RefusalStopEvent:
        """Truncate the history to the model's own window, refusing a turn that cannot fit it.

        Truncation alone cannot bound the prompt: `ChatMemoryBuffer.get` falls through to `chat_history[-1:]`
        when a single message exceeds the limit (llama-index-core 0.14.22), and `number_of_input_tokens` is an
        admin's cost ceiling that may sit above the model's real window. A chat client that pastes a whole
        document into one turn -- OpenWebUI does exactly this under `RAG_FULL_CONTEXT` -- therefore reaches the
        provider regardless.

        Unlike the RAG blueprints, this agent cannot fall back on the provider's own 400: it answers through
        `astream_chat`, and on a streaming call LiteLLM replaces the provider's message with its own bookkeeping
        (verified against gemma-4-31B-it on Infomaniak -- the same prompt returns "maximum context length is 100016
        tokens" unstreamed and a bare "Error code: 400" streamed), leaving `ModelGatewayErrorHandler` nothing to
        match.
        So the refusal has to happen here or not at all.
        """
        locale = event.locale
        system_messages = [msg for msg in event.messages if msg.role == MessageRole.SYSTEM]
        system_prompt = ChatMessage(role=MessageRole.SYSTEM, content=agent_config.system_prompt.in_locale(locale))
        regular_messages = [msg for msg in event.messages if msg.role != MessageRole.SYSTEM]
        # Only one leading system message may survive: strict providers (e.g. Qwen3.5 on Infomaniak) reject a
        # 400 "System message must be at the beginning" for any system message past index 0, and the chat
        # client's own system prompt (OpenWebUI model prompt, bot PathEntity.system_message) would push ours
        # to index 1. Merge before limiting so the token budget reflects what is actually sent.
        chat_history = merge_consecutive_messages(
            [
                *system_messages,
                system_prompt,
                *regular_messages,
            ]
        )
        # Merging has fused every system message -- the client's and ours -- into a single one at index 0, so the
        # head is the agent's instructions and the tail is the conversation. They are held apart from here on:
        # `ChatMemoryBuffer` keeps the most recent messages with no regard for role, so a history long enough to
        # trim would otherwise drop the system prompt and quietly leave the agent uninstructed.
        system_head, conversation = chat_history[:1], chat_history[1:]

        budget = usable_input_budget([agent_config.llm, agent_config.task_llm])
        if budget is None:
            limited = limit_chat_history(
                chat_history=conversation, number_of_input_tokens=agent_config.number_of_input_tokens
            )
            return Conversation.contextualize(history=[*system_head, *limited], message=event)

        # The system prompt and the last turn are what must be sent; everything between them is negotiable. Note
        # the merged last message rather than `event.last_user_message` -- this is the turn that actually goes out,
        # and the two differ whenever the client appends a trailing system message that merging folds into it.
        irreducible = [*system_head, *conversation[-1:]]
        irreducible_tokens = estimate_prompt_tokens(irreducible, agent_config.llm.token_counter)
        if irreducible_tokens > budget:
            return await OversizedInputRefusal.refuse(
                irreducible_tokens, budget, agent_config.llm.model_name, displayer, t
            )

        # Trim only what sits between them, then put both back. Handing the trimmer a list that still holds the
        # last turn charges it twice: no subset containing it fits the reduced limit, so `ChatMemoryBuffer` falls
        # through to its most-recent-message branch and drops the whole earlier conversation.
        older_limit = min(agent_config.number_of_input_tokens, budget - irreducible_tokens)
        older = (
            limit_chat_history(chat_history=conversation[:-1], number_of_input_tokens=older_limit)
            if older_limit > 0
            else []
        )
        return Conversation.contextualize(history=[*system_head, *older, *conversation[-1:]], message=event)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.gather_context.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.gather_context.description"),
        icon="mdi:brain",
    )
    async def gather_context_step(
        self, ctx: Conversation.Contextualized, event: UserMessageEvent, config: KnowledgeFields
    ) -> list[Memory.RecallRequest | AttachedFiles.ReadRequest | Knowledge.SearchRequest]:
        references = event.knowledge_references
        reserve = config.knowledge.context_reserve() if references else 0
        return [
            Memory.recall(ctx.query),
            AttachedFiles.read(event.files, ctx.history, ctx.query, reserve_tokens=reserve),
            Knowledge.search(references, ctx.query),
        ]

    @step(
        name=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.name"),
        description=AgentLocaleString.from_i18n_path("agent.conversation.steps.assemble_prompt.description"),
        icon="mdi:database-plus",
    )
    async def assemble_prompt_step(
        self,
        ctx: Conversation.Contextualized,
        memories: Memory.Recalled,
        files: AttachedFiles.Contents,
        knowledge: Knowledge.Searched,
    ) -> Conversation.ComposeRequest:
        return Conversation.compose(ctx.history, blocks=[*memories.blocks, knowledge.block, files.block])

    @step(
        name=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.start.name"),
        description=AgentLocaleString.from_i18n_path("agent.llm_wrapping_agent.steps.start.description"),
        icon="mage:message",
    )
    async def respond_step(
        self,
        event: Conversation.Composed,
        ctx: Conversation.Contextualized,
        agent_config: LLMWrappingAgentConfig,
        displayer: EventDisplayer,
        topic: AgentInstanceTopic,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[MemoryStorageRequestedEvent | Conversation.CompleteRequest]:
        """Stream the answer, then hand the turn back: the memory delegation first, so it is published before
        the run tears down, and the completion last.

        The composed history carries each recalled block as its own system message behind the system prompt;
        merged here so it reaches strict providers (e.g. Qwen3.5 on Infomaniak) as the single leading system
        message they accept.
        """
        history = merge_consecutive_messages(event.history)
        async with agent_config.llm.cost_reporting_llm(displayer, user=user) as llm:
            answer = await displayer.display_llm_stream(agent_config.llm, llm, history, as_stop_step=False)
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
