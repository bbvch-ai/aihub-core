from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    LimitChatHistoryEvent,
    StandaloneQuestionCondenserEvent,
    StopEvent,
)
from aihub_lib.nats.events.guard import (
    ContextInsufficientRejectEvent,
    ContextSufficientAcceptEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.InsightRetrievalAgent.events import (
    InsightRetrievalResponseEvent,
    InsightRetrievalStartEvent,
)
from aihub_agent.agents.KnowledgeRetrievalAgent.events import (
    KnowledgeRetrievalResponseEvent,
    KnowledgeRetrievalStartEvent,
)
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.events import RAGUserMessageEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.events import (
    CombinedRetrievalEvent,
    ContextInsufficientWithQueryEvent,
    LimitChatHistoryWithContextEvent,
)
from aihub_agent.rag.steps import (
    execute_condense_standalone_question,
    execute_context_sufficient_guard,
    execute_few_shot_guard,
    execute_limit_chat_history,
    execute_limit_chat_history_with_context,
    execute_order_nodes_by_documents,
    execute_rerank_nodes,
    execute_respond_with_llm,
)
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def all_retrievals_complete(
    agent_config: RAGAgentConfig,
    knowledge_responses: list[AgentInTheLoop.response] | None = None,
    insight_responses: list[AgentInTheLoop.response] | None = None,
) -> bool:
    """
    Precondition that waits for all retrieval agents to complete.

    Returns True when:
    - All configured knowledge retrieval agents have returned responses
    - All configured insight retrieval agents have returned responses
    """
    expected_knowledge = len(agent_config.knowledge_retrieval_agents)
    actual_knowledge = len(knowledge_responses) if knowledge_responses else 0
    knowledge_done = actual_knowledge >= expected_knowledge

    expected_insights = len(agent_config.insight_retrieval_agents)
    actual_insights = len(insight_responses) if insight_responses else 0
    insights_done = actual_insights >= expected_insights

    return knowledge_done and insights_done


@precondition()
async def context_ready_for_history_limit(
    context_event: CombinedRetrievalEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Requires CombinedRetrievalEvent AND ContextSufficientAcceptEvent.
    """
    return context_sufficient_event is not None


class RAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent.

    The RAGAgent orchestrates steps to process user input, retrieve relevant information
    from multiple knowledge retrieval agents and insight retrieval agents, condense questions,
    and generate responses using a configured language model.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Multi-agent knowledge retrieval via KnowledgeRetrievalAgent (referenced by ID).
    - Multi-agent insight retrieval via InsightRetrievalAgent (referenced by ID).
    - Combined reranking of all retrieved nodes.
    - Generate responses using an LLM based on the context and retrieved information.

    Note: This is the simple RAG agent without expert escalation.
    For expert escalation support, use ExpertRAGAgent.
    """

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        """Truncates incoming chat messages to fit within the configured token limit."""
        return execute_limit_chat_history(
            messages=event.messages,
            number_of_input_tokens=agent_config.number_of_input_tokens,
        )

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: RAGAgentConfig,
        t: LocaleHandler,
        displayer: EventDisplayer,
    ) -> StandaloneQuestionCondenserEvent:
        """Condenses the chat history and user query into a standalone question."""
        return await execute_condense_standalone_question(
            limited_history=event.limited_history,
            user_query=start_event.user_query,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            condense_prompt=agent_config.condense_question_prompt,
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
        """Guards the question to ensure it is appropriate for the agent to answer."""
        return await execute_few_shot_guard(
            condensed_question=event.condensed_chat_message.content,
            few_shot_examples=agent_config.few_shot_guard_examples,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
        )

    @step(
        name=LocaleString(en="Invoke Knowledge Retrieval Agents"),
        description=LocaleString(en="Invokes KnowledgeRetrievalAgent for each configured agent."),
        icon="hugeicons:robot-02",
    )
    async def invoke_knowledge_retrieval_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> list[AgentInTheLoop.request] | None:
        """Invokes KnowledgeRetrievalAgent for each configured agent ID."""
        if not agent_config.knowledge_retrieval_agents:
            return None

        await displayer.display_thought(t("agent.thought.searching_knowledge"))

        query = (
            event.condensed_chat_message.content
            if isinstance(event, StandaloneQuestionCondenserEvent)
            else event.new_query
        )

        # Build override lookup from event if RAGUserMessageEvent
        override_lookup: dict[str, list[str]] = {}
        if isinstance(start_event, RAGUserMessageEvent) and start_event.knowledge_overrides:
            override_lookup = {o.agent_id: o.namespaces for o in start_event.knowledge_overrides}

        requests = []
        for agent_id in agent_config.knowledge_retrieval_agents:
            # Use override namespaces if provided
            namespaces = override_lookup.get(agent_id)

            requests.append(
                AgentInTheLoop.invoke(
                    agent_class="KnowledgeRetrievalAgent",
                    agent_id=agent_id,
                    start_event=KnowledgeRetrievalStartEvent(
                        question=query,
                        locale=start_event.locale,
                        namespaces=namespaces,
                    ),
                )
            )

        return requests

    @step(
        name=LocaleString(en="Invoke Insight Retrieval Agents"),
        description=LocaleString(en="Invokes InsightRetrievalAgent for each configured agent."),
        icon="hugeicons:robot-02",
    )
    async def invoke_insight_retrieval_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> list[AgentInTheLoop.request] | None:
        """Invokes InsightRetrievalAgent for each configured agent ID."""
        if not agent_config.insight_retrieval_agents:
            return None

        query = (
            event.condensed_chat_message.content
            if isinstance(event, StandaloneQuestionCondenserEvent)
            else event.new_query
        )

        # Use override sources if provided
        sources = None
        if isinstance(start_event, RAGUserMessageEvent) and start_event.insight_overrides:
            sources = start_event.insight_overrides

        requests = []
        for agent_id in agent_config.insight_retrieval_agents:
            requests.append(
                AgentInTheLoop.invoke(
                    agent_class="InsightRetrievalAgent",
                    agent_id=agent_id,
                    start_event=InsightRetrievalStartEvent(
                        question=query,
                        locale=start_event.locale,
                        sources=sources,
                    ),
                )
            )

        return requests

    @step(
        name=LocaleString(en="Combine Retrieval Results"),
        description=LocaleString(en="Combines results from all retrieval agents and applies reranking."),
        precondition=all_retrievals_complete,
    )
    async def combine_retrieval_results_step(
        self,
        agent_config: RAGAgentConfig,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        condenser_event: StandaloneQuestionCondenserEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
        knowledge_responses: list[AgentInTheLoop.response] | None = None,
        insight_responses: list[AgentInTheLoop.response] | None = None,
    ) -> CombinedRetrievalEvent:
        """Combines results from all retrieval agents and applies shared reranking."""
        all_nodes = []
        knowledge_agent_ids = []

        # Collect nodes from knowledge responses
        if knowledge_responses:
            for response in knowledge_responses:
                if isinstance(response.stop_event, KnowledgeRetrievalResponseEvent):
                    all_nodes.extend(response.stop_event.nodes)
                    knowledge_agent_ids.append(response.stop_event.agent_id)

        # Collect nodes from insight responses
        has_insights = False
        if insight_responses:
            for response in insight_responses:
                if isinstance(response.stop_event, InsightRetrievalResponseEvent):
                    all_nodes.extend(response.stop_event.nodes)
                    has_insights = True

        # Apply shared reranking if enabled
        if agent_config.reranking_config.enabled and all_nodes:
            query = condenser_event.condensed_chat_message.content
            reranker_event = await execute_rerank_nodes(
                nodes=all_nodes,
                query=query,
                reranking_model=agent_config.reranking_config.reranking_model,
                displayer=displayer,
                t=t.in_locale(start_event.locale),
                reranking_enabled=True,
            )
            all_nodes = reranker_event.output_nodes

        # Order nodes by documents and create context message
        order_event = await execute_order_nodes_by_documents(
            nodes=all_nodes,
            t=t.in_locale(start_event.locale),
            displayer=displayer,
            context_prompt=None,
        )

        return CombinedRetrievalEvent(
            context_message=order_event.context_message,
            nodes=all_nodes,
            knowledge_agent_ids=knowledge_agent_ids,
            has_insights=has_insights,
        )

    @step(
        name=LocaleString(en="Retrieval Error"),
        description=LocaleString(en="Handles errors from retrieval agents."),
    )
    async def retrieval_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handles errors from retrieval agents."""
        await displayer.display_thought(
            t(
                "agent.rag_agent.thoughts.retrieval_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(t("agent.rag_agent.messages.retrieval_error"), model_name="RAG Agent")
        return StopEvent()

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        event: CombinedRetrievalEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> ContextSufficientAcceptEvent | ContextInsufficientRejectEvent | ContextInsufficientWithQueryEvent:
        """Guards the context to ensure it is sufficient for generating a response."""
        return await execute_context_sufficient_guard(
            context_content=event.context_message.content or "",
            user_query=user_query_event.condensed_chat_message.content or "",
            check_context_sufficiency=agent_config.check_context_sufficiency or False,
            max_hops=agent_config.max_hops,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            run_context=run_context,
        )

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
        precondition=context_ready_for_history_limit,
    )
    async def limit_chat_history_with_context_step(
        self,
        context_event: CombinedRetrievalEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | RAGUserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """Includes the combined context and truncates chat history again."""
        return execute_limit_chat_history_with_context(
            chat_history=chat_history_event.limited_history,
            context_message=context_event.context_message,
            last_user_message=start_event.last_user_message,
            llm_config=agent_config.llm,
            number_of_input_tokens=agent_config.number_of_input_tokens,
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
    ) -> LLMStopEvent:
        """Generates a response using the configured LLM."""
        if isinstance(event, FewShotRejectEvent | ContextInsufficientRejectEvent):
            messages = limited_history_without_context.limited_history
            reject_reason = event.reason
        else:
            messages = event.limited_history_with_context
            reject_reason = None

        return await execute_respond_with_llm(
            messages=messages,
            llm_config=agent_config.llm,
            t=t,
            displayer=displayer,
            system_prompt=agent_config.system_prompt,
            reject_reason=reject_reason,
        )
