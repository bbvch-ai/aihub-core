from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
)
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.preconditions import (
    check_context_ready_for_history_limit,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
)
from aihub_agent.rag.step_functions import (
    do_context_sufficient_guard,
    do_few_shot_guard,
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


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information,
    condense questions, and generate responses using a configured language model and retrieval setup.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: For expert escalation functionality, use ExpertRAGAgent instead.
    """

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        """
        Truncates incoming chat messages to fit within the configured token limit
        """
        limited_chat_history = limit_chat_history(
            chat_history=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryEvent(limited_history=limited_chat_history)

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        """
        Condenses the chat history and user query into a standalone question.
        """
        await displayer.display_thought(t("agent.thought.condense_question"))
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            condensed_question = condense_standalone_question(
                chat_history=event.limited_history, message=start_event.last_user_message, t=t, llm=llm
            )
            return StandaloneQuestionCondenserEvent(condensed_chat_message=condensed_question)

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
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await do_few_shot_guard(
                condensed_question=event.condensed_chat_message.content,
                examples=agent_config.few_shot_guard_examples,
                llm=llm,
                t=t,
            )

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """Retrieves relevant nodes from multiple knowledge sources in parallel."""
        return await do_retrieve(event, agent_config.retrievers, t)

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
        await displayer.display_thought(t("agent.thought.reranking_results"))
        return await do_rerank_nodes(
            nodes=event.nodes,
            query=condense_event.condensed_chat_message.content,
            reranking_config=agent_config.reranking_config,
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
        """
        Orders the retrieved nodes based on their source documents.
        """
        await displayer.display_thought(t("agent.thought.searching_knowledge"))
        ordered_nodes = do_order_nodes_by_documents(event, t, agent_config.context_prompt)
        return InOrderNodeCombinerEvent(context_message=ordered_nodes)

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
        """
        Guards the context to ensure it is sufficient for generating a response.
        If it is insufficient a new query is generated to find more data in order
        to generate the response.
        """
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await do_context_sufficient_guard(
                user_query=user_query_event.condensed_chat_message.content,
                context=event.context_message.content,
                check_context_sufficiency=agent_config.check_context_sufficiency,
                max_hops=agent_config.max_hops,
                run_context=run_context,
                llm=llm,
                displayer=displayer,
                t=t,
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
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Includes the combined context and truncates chat history again.
        """
        limited_chat_history = do_limit_chat_history_with_context(
            context_message=context_event.context_message,
            chat_history=chat_history_event.limited_history,
            last_user_message=start_event.last_user_message,
            tokenizer=agent_config.llm.token_counter,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )
        return LimitChatHistoryWithContextEvent(limited_history_with_context=limited_chat_history)

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
    ) -> LLMStopEvent:
        """Generates a response using the configured LLM."""
        return await do_respond_with_llm(
            event=event,
            limited_history_without_context=limited_history_without_context.limited_history,
            context_insufficient_prompt=agent_config.context_insufficient_prompt,
            system_prompt=agent_config.system_prompt,
            llm_config=agent_config.llm,
            displayer=displayer,
            t=t,
        )
