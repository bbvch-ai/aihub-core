from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.guards.context_sufficient_guard import context_sufficient_guard
from aihub_lib.generative_ai.guards.few_shot_guard import few_shot_guard
from aihub_lib.generative_ai.knowledge.RetrieverFactory import create_retriever
from aihub_lib.generative_ai.resources.models.llm.message_preprocessor import merge_consecutive_messages
from aihub_lib.generative_ai.utils.combine_nodes_in_order import combine_nodes_in_order
from aihub_lib.generative_ai.utils.condense_standalone_question import condense_standalone_question
from aihub_lib.generative_ai.utils.limit_chat_history import limit_chat_history
from aihub_lib.generative_ai.utils.limit_chat_history_with_context import limit_chat_history_with_context
from aihub_lib.generative_ai.utils.rerank_nodes import rerank_nodes
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    HumanInTheLoop,
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
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent
from llama_index.core import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from llama_index.core.prompts.rich import RichPromptTemplate

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AnswerStopEvent import AnswerStopEvent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertAskingAgent.events.NoAnswerStopEvent import NoAnswerStopEvent
from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.ExpertEscalationEvent import ExpertEscalationEvent
from aihub_agent.agents.RagAgent.events.FormulatedQuestionEvent import FormulatedQuestionEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.RagAgent.events.UserConsentEvent import UserConsentEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def reranking_enabled(event: RetrieverEvent, config: RAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return isinstance(event, RetrieverEvent) and config.reranking_config.enabled


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: RAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    # If reranking is disabled, we can proceed with RetrieverEvent
    if not config.reranking_config.enabled:
        return isinstance(event, RetrieverEvent)
    # If reranking is enabled, we must wait for RerankerEvent
    return isinstance(event, RerankerEvent)


@precondition()
async def is_expert_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer from ExpertAskingAgent."""
    return isinstance(event.stop_event, AnswerStopEvent)


@precondition()
async def is_expert_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful answer from ExpertAskingAgent."""
    return isinstance(event.stop_event, NoAnswerStopEvent)


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
        user_query = start_event.user_query
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            condensed_question = condense_standalone_question(
                chat_history=event.limited_history,
                message=user_query,
                t=t,
                llm=llm,
                condense_prompt=agent_config.condense_question_prompt,
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
        if not agent_config.few_shot_guard_examples:
            return FewShotAcceptEvent(reason=t("agent.thought.no_few_shot_examples"))

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            guard_result = await few_shot_guard(
                llm=llm,
                t=t,
                user_query=event.condensed_chat_message.content,
                examples=agent_config.few_shot_guard_examples,
            )

        if not guard_result.success:
            return FewShotRejectEvent(reason=guard_result.reasoning)

        return FewShotAcceptEvent(reason=guard_result.reasoning)

    @step(
        name=LocaleString(en="Retrieve Nodes"),
        description=LocaleString(en="Retrieves relevant nodes from knowledge sources."),
    )
    async def retrieve_step(
        self,
        event: StandaloneQuestionCondenserEvent | ContextInsufficientWithQueryEvent,
        _: FewShotAcceptEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RetrieverEvent:
        """
        Retrieves relevant nodes from multiple knowledge sources.

        Iterates through configured retrievers (knowledge base, insights)
        and combines all retrieved nodes.
        """
        if isinstance(event, StandaloneQuestionCondenserEvent):
            query = event.condensed_chat_message.content
        else:
            query = event.new_query

        all_nodes = []
        for retriever_config in agent_config.retrievers:
            if not retriever_config.enabled:
                continue

            retriever = create_retriever(retriever_config)
            await displayer.display_thought(t("agent.thought.retrieving_from", source=retriever.name))
            nodes = await retriever.retrieve(query)
            all_nodes.extend(nodes)

        # Convert IngestedNodes to NodeWithScore for downstream processing
        nodes_with_score = [node.to_llama_index_node_with_score() for node in all_nodes]
        return RetrieverEvent.from_nodes(nodes_with_score)

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

        reranked_nodes = await rerank_nodes(
            nodes=event.nodes,
            query=condense_event.condensed_chat_message.content,
            reranking_model=agent_config.reranking_config.reranking_model,
        )

        return RerankerEvent(
            query=condense_event.condensed_chat_message.content,
            rerank_model_name=agent_config.reranking_config.reranking_model.model_name,
            top_n=agent_config.reranking_config.reranking_model.top_n,
            input_nodes=event.nodes,
            output_nodes=reranked_nodes,
            reranked=agent_config.reranking_config.enabled,
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
        nodes = event.output_nodes if isinstance(event, RerankerEvent) else event.nodes
        ordered_nodes = combine_nodes_in_order(
            context_nodes=nodes,
            t=t,
            context_prompt=agent_config.context_prompt,
        )
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
        retriever_event: RetrieverEvent,
        user_query_event: StandaloneQuestionCondenserEvent,
        run_context: RunContext,
    ) -> (
        ContextSufficientAcceptEvent
        | ContextInsufficientRejectEvent
        | ContextInsufficientWithQueryEvent
        | ExpertEscalationEvent
    ):
        """
        Guards the context to ensure it is sufficient for generating a response.
        If insufficient, either tries another retrieval hop, escalates to experts,
        or rejects.
        """
        if not agent_config.check_context_sufficiency:
            return ContextSufficientAcceptEvent(reason=t("agent.thought.no_context_sufficiency_check"))

        prev_queries = await run_context.get("prev_queries", [])
        hop_count = await run_context.get("hop_count", 1)
        more_hops_available = hop_count < agent_config.max_hops

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            guard_result = await context_sufficient_guard(
                llm=llm,
                t=t,
                user_query=user_query_event.condensed_chat_message.content,
                context=event.context_message.content,
                prev_queries=prev_queries,
                more_hops_available=more_hops_available,
            )

        if guard_result.success:
            await displayer.display_thought(t("agent.thought.context_sufficient"))
            return ContextSufficientAcceptEvent(reason=guard_result.reasoning)

        # Context is insufficient - try more hops if available
        if more_hops_available:
            await run_context.set("hop_count", hop_count + 1)
            new_query = guard_result.new_query
            prev_queries.append(new_query)
            await run_context.set("prev_queries", prev_queries)
            await displayer.display_thought(t("agent.thought.trying_another_retrieval_hop"))
            return ContextInsufficientWithQueryEvent(reason=guard_result.reasoning, new_query=new_query)

        # No more hops - check if expert workflow is enabled
        expert_config = agent_config.expert_workflow_config
        if expert_config and expert_config.enabled:
            await displayer.display_thought(t("agent.rag_agent.thoughts.escalating_to_expert"))
            nodes = retriever_event.nodes or []
            await run_context.set("retrieved_nodes", [node.model_dump() for node in nodes])
            return ExpertEscalationEvent(reason=guard_result.reasoning)

        return ContextInsufficientRejectEvent(reason=guard_result.reasoning)

    @step(
        name=LocaleString(en="Limit Chat History with Context"),
        description=LocaleString(en="Includes the combined context and truncates chat history again."),
    )
    async def limit_chat_history_with_context_step(
        self,
        nodes_event: InOrderNodeCombinerEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent,
        start_event: UserMessageEvent,
        agent_config: RAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        """
        Includes the combined context and truncates chat history again.
        """
        chat_history = chat_history_event.limited_history
        system_messages = [msg for msg in chat_history if msg.role == MessageRole.SYSTEM]
        limited_chat_history = limit_chat_history_with_context(
            chat_history=chat_history_event.limited_history,
            context_messages=[nodes_event.context_message],
            system_messages=system_messages,
            last_user_message=start_event.last_user_message or ChatMessage(role=MessageRole.USER, content=""),
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
        """
        Generates a response using the configured LLM.
        """
        if isinstance(event, FewShotRejectEvent) or isinstance(event, ContextInsufficientRejectEvent):
            messages = limited_history_without_context.limited_history + [
                ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=PromptTemplate(t("agent.prompt.guard.reject")).format(reason=event.reason),
                ),
            ]
        else:
            messages = event.limited_history_with_context
        await displayer.display_thought(t("agent.thought.write_answer_based_on_information"))

        system_prompt_text = t.extract(agent_config.system_prompt) if agent_config.system_prompt else None
        if system_prompt_text:
            system_message = ChatMessage(role=MessageRole.SYSTEM, content=system_prompt_text)
            messages = [system_message] + messages

        # Merge consecutive messages with the same role (required by LiteLLM)
        messages = merge_consecutive_messages(messages)

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            return await displayer.display_llm_stream(agent_config.llm, llm, messages, as_stop_step=True)

    # ========================================================================
    # Expert Workflow Steps (Optional - only active when expert_workflow_config.enabled)
    # ========================================================================

    @step(
        name=LocaleString(en="Formulate Expert Question"),
        description=LocaleString(en="Formulates a specific question for the expert based on missing context."),
        icon="mdi:comment-question",
    )
    async def formulate_expert_question_step(
        self,
        event: UserMessageEvent,
        _: ExpertEscalationEvent,
        agent_config: RAGAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> FormulatedQuestionEvent:
        """Formulates a specific question for the expert based on missing context."""
        await displayer.display_thought(t("agent.rag_agent.thoughts.formulating_question"))

        user_query = event.messages[-1].content
        chat_history = event.messages[:-1]

        # Get retrieved nodes for context
        nodes_data = await run_context.get("retrieved_nodes", [])
        nodes = [IngestedNode(**node) for node in nodes_data]

        # Build context from nodes (limit to half for question formulation)
        context_text = ""
        expert_config = agent_config.expert_workflow_config
        if nodes and expert_config:
            max_nodes = max(1, expert_config.max_context_nodes_for_expert // 2)
            context_parts = [f"- {node.content}" for node in nodes[:max_nodes]]
            context_text = "\n".join(context_parts)

        # Use LLM to formulate a specific question for the expert
        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            prompt = RichPromptTemplate(template_str=t("agent.rag_agent.formulate_question_prompt")).format_messages(
                chat_history=chat_history,
                user_query=user_query,
                context=context_text,
            )
            response: ChatResponse = await llm.achat(prompt)
            formulated_question = response.message.content or ""

        await run_context.set("formulated_question", formulated_question)
        return FormulatedQuestionEvent(question=formulated_question)

    @step(
        name=LocaleString(en="Ask for Consent"),
        description=LocaleString(en="Ask user for consent to contact expert with the formulated question."),
        icon="akar-icons:chat-approve",
    )
    async def ask_consent_step(
        self,
        event: FormulatedQuestionEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.request:
        """Ask user for consent to contact expert."""
        await displayer.display_thought(t("agent.rag_agent.thoughts.asking_for_consent"))
        consent_message = t(
            "agent.rag_agent.messages.consent_question",
            question=event.question,
        )
        return HumanInTheLoop.invoke(question=consent_message)

    @step(
        name=LocaleString(en="Process Consent Answer"),
        description=LocaleString(en="User answered the question for consent."),
        icon="carbon:question-answering",
    )
    async def user_consent_response_step(
        self,
        event: HumanInTheLoop.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserConsentEvent | StopEvent:
        """Process user's consent response."""
        if "yes" in event.response.lower() or "ja" in event.response.lower():
            await displayer.display_thought(t("agent.rag_agent.thoughts.user_consented"))
            return UserConsentEvent()
        await displayer.display_thought(t("agent.rag_agent.thoughts.user_declined"))
        await displayer.display_chunk(t("agent.rag_agent.messages.user_declined"), model_name="gpt-4o")
        return StopEvent()

    @step(
        name=LocaleString(en="Forward to Expert"),
        description=LocaleString(en="Forwarding request to ExpertAskingAgent."),
        icon="hugeicons:robot-02",
    )
    async def forward_to_expert_step(
        self,
        user_message_event: UserMessageEvent,
        formulated_question_event: FormulatedQuestionEvent,
        _: UserConsentEvent,
        displayer: EventDisplayer,
        agent_config: RAGAgentConfig,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Forward the question to ExpertAskingAgent."""
        await displayer.display_thought(t("agent.rag_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(t("agent.rag_agent.messages.expert_forwarding"), model_name="expert")

        # Get retrieved nodes to pass to ExpertAskingAgent
        nodes_data = await run_context.get("retrieved_nodes", [])
        nodes = [IngestedNode(**node) for node in nodes_data]

        expert_config = agent_config.expert_workflow_config
        if not expert_config:
            raise ValueError("Expert workflow config is required but not configured")

        return AgentInTheLoop.invoke(
            agent_class=expert_config.expert_asking_agent_class,
            agent_id=expert_config.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=formulated_question_event.question,
                locale=user_message_event.locale,
                user=user_message_event.user,
                nodes=nodes,
            ),
        )

    @step(
        precondition=is_expert_answer_response,
        name=LocaleString(en="Expert Answered"),
        description=LocaleString(en="ExpertAskingAgent received an answer from expert."),
        icon="ix:user-success-filled",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handle successful expert answer."""
        await displayer.display_thought(t("agent.rag_agent.thoughts.expert_answered"))
        await displayer.display_chunk(event.stop_event.expert_answer, model_name="expert")
        return StopEvent()

    @step(
        precondition=is_expert_no_answer_response,
        name=LocaleString(en="Expert Unable to Answer"),
        description=LocaleString(en="ExpertAskingAgent could not get an answer from expert."),
        icon="ix:user-fail-filled",
    )
    async def expert_not_answered_step(
        self,
        displayer: EventDisplayer,
        _: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handle case when expert couldn't answer."""
        await displayer.display_thought(t("agent.rag_agent.thoughts.expert_unable_to_answer"))
        await displayer.display_chunk(t("agent.rag_agent.messages.expert_unable_to_answer"), model_name="expert")
        return StopEvent()

    @step(
        name=LocaleString(en="Expert Error"),
        description=LocaleString(en="ExpertAskingAgent encountered an error."),
        icon="ix:error",
    )
    async def expert_exception_step(
        self,
        displayer: EventDisplayer,
        exception_event: AgentInTheLoop.exception,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handle errors from ExpertAskingAgent."""
        await displayer.display_thought(
            t(
                "agent.rag_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        await displayer.display_chunk(t("agent.rag_agent.messages.expert_error"), model_name="expert")
        return StopEvent()
