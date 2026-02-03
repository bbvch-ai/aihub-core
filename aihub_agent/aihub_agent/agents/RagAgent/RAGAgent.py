from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.chat_history.extend_chat_history_with_organization_memory import (
    extend_chat_history_with_organization_memory,
)
from aihub_lib.generative_ai.chat_history.extend_chat_history_with_user_memory import (
    extend_chat_history_with_user_memory,
)
from aihub_lib.generative_ai.memory.AgentMemory import AgentMemory
from aihub_lib.generative_ai.utils.filter_retrievers_by_namespace import filter_retrievers_by_namespace
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
)
from aihub_lib.nats.events.control.stop.StopEvent import StopEvent
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.memory.history.AddMemoryToChatHistoryEvent import AddMemoryToChatHistoryEvent
from aihub_lib.nats.events.memory.retrieve.RetrieveOrganizationMemoryEvent import RetrieveOrganizationMemoryEvent
from aihub_lib.nats.events.memory.retrieve.RetrieveUserMemoryEvent import RetrieveUserMemoryEvent
from aihub_lib.nats.events.memory.store.StoreUserMemoryEvent import StoreUserMemoryEvent
from aihub_lib.nats.events.semantic.llm import LLMEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.topics import AgentInstanceTopic

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.RagAgent.events.NamespaceAwareUserMessageEvent import NamespaceAwareUserMessageEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.preconditions import (
    check_context_ready_for_history_limit,
    check_memory_added_to_chat_history,
    check_memory_ready_for_chat_history,
    check_organization_memory_enabled,
    check_ready_for_stop,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
    check_user_memory_retrieval_enabled,
    check_user_memory_storage_enabled,
)
from aihub_agent.rag.step_functions import (
    do_condense_standalone_question,
    do_context_sufficient_guard,
    do_few_shot_guard,
    do_limit_chat_history,
    do_limit_chat_history_with_context,
    do_order_nodes_by_documents,
    do_rerank_nodes,
    do_respond_with_llm,
    do_retrieve,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: RAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config.enabled)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config.enabled)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when InOrderNodeCombinerEvent is present AND ContextSufficientAcceptEvent is present.
    """
    return check_context_ready_for_history_limit(context_event, context_sufficient_event)


@precondition()
async def organization_memory_enabled(config: RAGAgentConfig) -> bool:
    """Precondition to check if organization memory retrieval is enabled."""
    return check_organization_memory_enabled(config)


@precondition()
async def user_memory_retrieval_enabled(config: RAGAgentConfig) -> bool:
    """Precondition to check if user memory retrieval is enabled."""
    return check_user_memory_retrieval_enabled(config)


@precondition()
async def user_memory_storage_enabled(config: RAGAgentConfig) -> bool:
    """Precondition to check if user memory storage is enabled."""
    return check_user_memory_storage_enabled(config)


@precondition()
async def memory_ready_for_chat_history(
    config: RAGAgentConfig,
    user_memory_event: RetrieveUserMemoryEvent | None = None,
    org_memory_event: RetrieveOrganizationMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required memory events are present before extending chat history."""
    return check_memory_ready_for_chat_history(config, user_memory_event, org_memory_event)


@precondition()
async def memory_added_to_chat_history(
    config: RAGAgentConfig,
    memory_history_event: AddMemoryToChatHistoryEvent | None = None,
) -> bool:
    """Precondition to ensure memory has been added to chat history when required."""
    return check_memory_added_to_chat_history(config, memory_history_event)


@precondition()
async def ready_for_stop(
    config: RAGAgentConfig,
    store_memory_event: StoreUserMemoryEvent | None = None,
) -> bool:
    """Precondition to ensure all required steps are complete before stopping."""
    return check_ready_for_stop(config, store_memory_event)


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Retrieve user memories (personalized context) for individualized responses
    - Retrieve organization memories (expert knowledge) for shared context
    - Store new user memories from conversations for future retrieval
    - Limit chat history to fit input token limits
    - Condense chat history into standalone question
    - Retrieve relevant documents from a knowledge base
    - Order retrieved nodes for better contextual relevance
    - Generate responses using an LLM based on the context and retrieved information

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    @step(
        name=LocaleString(en="Retrieve User Memory"),
        description=LocaleString(en="Retrieves relevant user-specific memories for personalized context"),
        icon="mdi:account-circle",
        precondition=user_memory_retrieval_enabled,
    )
    async def retrieve_user_memory_step(
        self,
        event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        memory: AgentMemory,
    ) -> RetrieveUserMemoryEvent:
        """Retrieve user memories for personalized context."""
        query = event.user_query
        memory_result = await memory.search_user_memory(
            query=query,
            user_id=event.user.id,
            limit=10,
            threshold=0.5,
            rerank=True,
        )

        return RetrieveUserMemoryEvent.from_memory_search_result(memory_result)

    @step(
        name=LocaleString(en="Retrieve Organization Memory"),
        description=LocaleString(en="Retrieves relevant organization memories (expert knowledge) based on user query"),
        icon="mdi:brain",
        precondition=organization_memory_enabled,
    )
    async def retrieve_organization_memory_step(
        self,
        event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: RAGAgentConfig,
        memory: AgentMemory,
    ) -> RetrieveOrganizationMemoryEvent:
        """Retrieve organization memories for expert knowledge context."""
        query = event.user_query
        memory_result = await memory.search_organization_memory(
            query=query,
            tenant_id=agent_config.tenant_id,
            tenant_namespace=agent_config.tenant_namespace,
            user_id=event.user.id,
            limit=10,
            threshold=0.5,
            rerank=True,
        )

        return RetrieveOrganizationMemoryEvent.from_memory_search_result(memory_result)

    @step(
        name=LocaleString(en="Add Memory to Context"),
        description=LocaleString(en="Injects user and organization memories into chat history as system messages"),
        icon="mdi:database-plus",
        precondition=memory_ready_for_chat_history,
    )
    async def add_memory_to_chat_history_step(
        self,
        user_message_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        user_memory_event: RetrieveUserMemoryEvent | None,
        org_memory_event: RetrieveOrganizationMemoryEvent | None,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
    ) -> AddMemoryToChatHistoryEvent:
        """Extend chat history with memory context (user and/or organization)."""
        chat_history = user_message_event.messages

        # Add user memory first (more personal context)
        if agent_config.enable_user_memory_retrieval and user_memory_event is not None:
            chat_history = extend_chat_history_with_user_memory(
                chat_history=chat_history,
                memories=user_memory_event.memories,
                relations=user_memory_event.relations,
                user=user_message_event.user,
                t=t,
            )

        # Add organization memory second (broader context)
        if agent_config.enable_organization_memory and org_memory_event is not None:
            chat_history = extend_chat_history_with_organization_memory(
                chat_history=chat_history,
                memories=org_memory_event.memories,
                relations=org_memory_event.relations,
                t=t,
            )

        return AddMemoryToChatHistoryEvent(extended_history=chat_history)

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
        precondition=memory_added_to_chat_history,
    )
    async def limit_chat_history_step(
        self,
        user_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        memory_history_event: AddMemoryToChatHistoryEvent | None,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        # Use extended history if memory was added, otherwise use original messages
        messages = memory_history_event.extended_history if memory_history_event is not None else user_event.messages
        return do_limit_chat_history(messages, agent_config.number_of_input_tokens)

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        return await do_condense_standalone_question(
            event.limited_history, start_event.last_user_message, agent_config.llm, displayer, t
        )

    @step(
        name=LocaleString(en="Few Shot Guard"),
        description=LocaleString(en="Guards the question to ensure it is appropriate for the agent to answer."),
    )
    async def few_shot_guard_step(
        self,
        event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FewShotRejectEvent | FewShotAcceptEvent:
        return await do_few_shot_guard(
            event.condensed_chat_message.content, agent_config.few_shot_guard_examples, agent_config.llm, displayer, t
        )

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        if isinstance(start_event, NamespaceAwareUserMessageEvent):
            retrievers = filter_retrievers_by_namespace(agent_config.retrievers, start_event.selected_namespaces)
        else:
            retrievers = agent_config.retrievers
        return await do_retrieve(event, retrievers, t)

    @step(
        name=LocaleString(en="Rerank Retrieved Nodes"),
        description=LocaleString(
            en="Reranks retrieved documents using a dedicated reranking model for improved relevance"
        ),
        icon="iconoir:sort-desc",
        precondition=reranking_enabled,
    )
    async def rerank_nodes_step(
        self,
        event: RetrieverEvent,
        condense_event: StandaloneQuestionCondenserEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RerankerEvent:
        return await do_rerank_nodes(
            event.nodes, condense_event.condensed_chat_message.content, agent_config.reranking_config, displayer, t
        )

    @step(
        name=LocaleString(en="Order Nodes by Documents"),
        description=LocaleString(en="Orders the retrieved nodes by their source documents."),
        precondition=reranking_complete_or_disabled,
    )
    async def order_nodes_by_documents_step(
        self,
        event: RetrieverEvent | RerankerEvent,
        t: LocaleHandler,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        return await do_order_nodes_by_documents(event, t, agent_config.context_prompt, displayer)

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: InOrderNodeCombinerEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        return await do_context_sufficient_guard(
            user_query_event.condensed_chat_message.content,
            event.context_message.content,
            agent_config.check_context_sufficiency,
            agent_config.max_hops,
            run_context,
            agent_config.llm,
            displayer,
            t,
        )

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        return do_limit_chat_history_with_context(
            context_event.context_message,
            chat_history_event.limited_history,
            start_event.last_user_message,
            agent_config.llm.token_counter,
            agent_config.number_of_input_tokens,
        )

    @step(
        name=LocaleString(en="Respond with LLM"),
        description=LocaleString(en="Generates a response using the configured LLM."),
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ContextInsufficientRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMEvent:
        # Use as_stop_step=False to return LLMEvent (not LLMStopEvent)
        # This allows store_user_memory_step to run before the final stop_step
        return await do_respond_with_llm(
            event,
            limited_history_without_context.limited_history,
            agent_config.context_insufficient_prompt,
            agent_config.system_prompt,
            agent_config.llm,
            displayer,
            t,
            as_stop_step=False,
        )

    @step(
        name=LocaleString(en="Store User Memory"),
        description=LocaleString(en="Persists conversation learnings to long-term user memory for future interactions"),
        icon="mdi:content-save",
        precondition=user_memory_storage_enabled,
    )
    async def store_user_memory_step(
        self,
        user_message_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        llm_event: LLMEvent,
        memory: AgentMemory,
        topic: AgentInstanceTopic,
    ) -> StoreUserMemoryEvent:
        """Store new user memories from the conversation."""
        memory_added = await memory.add_user_memory(
            messages=llm_event.chat_messages,
            user_id=user_message_event.user.id,
            thread_id=topic.thread_id,
            display_id=topic.display_id,
            run_id=topic.run_id,
        )
        return StoreUserMemoryEvent.from_memory_added_object(memory_added)

    @step(
        name=LocaleString(en="Stop"),
        description=LocaleString(en="Completes the workflow after all required steps are done"),
        precondition=ready_for_stop,
    )
    async def stop_step(
        self,
        _llm_event: LLMEvent,
        _store_memory_event: StoreUserMemoryEvent | None,
        agent_config: RAGAgentConfig,
    ) -> StopEvent:
        """Final step that ensures all required steps are complete before stopping."""
        return StopEvent()
