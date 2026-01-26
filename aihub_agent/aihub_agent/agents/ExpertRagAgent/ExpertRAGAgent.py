from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.utils.filter_retrievers_by_namespace import filter_retrievers_by_namespace
from aihub_lib.generative_ai.chat_history.format_expert_conversation import format_expert_conversation
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
    ExpertRejectEvent,
    FewShotAcceptEvent,
    FewShotRejectEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.semantic.reranker import RerankerEvent
from aihub_lib.nats.events.semantic.retriever import RetrieverEvent
from aihub_lib.nats.events.user import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.ExpertAskingAgent.events.AskExpertStartEvent import AskExpertStartEvent
from aihub_agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from aihub_agent.agents.RagAgent.events.ContextInsufficientWithQueryEvent import ContextInsufficientWithQueryEvent
from aihub_agent.agents.RagAgent.events.ExpertAnswerContextEvent import ExpertAnswerContextEvent
from aihub_agent.agents.RagAgent.events.InOrderNodeCombinerEvent import InOrderNodeCombinerEvent
from aihub_agent.agents.RagAgent.events.LimitChatHistoryWithContextEvent import LimitChatHistoryWithContextEvent
from aihub_agent.agents.RagAgent.events.NamespaceAwareUserMessageEvent import NamespaceAwareUserMessageEvent
from aihub_agent.agents.RagAgent.events.UserRequestsExpertEvent import UserRequestsExpertEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.rag.preconditions import (
    check_context_ready_for_history_limit_with_expert,
    check_is_answer_response,
    check_is_no_answer_response,
    check_reranking_complete_or_disabled,
    check_reranking_enabled,
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
async def reranking_enabled(event: RetrieverEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to check if reranking is enabled or not."""
    return check_reranking_enabled(event, config.reranking_config.enabled)


@precondition()
async def reranking_complete_or_disabled(event: RetrieverEvent | RerankerEvent, config: ExpertRAGAgentConfig) -> bool:
    """Precondition to ensure we only order nodes after reranking is complete (or if reranking is disabled)."""
    return check_reranking_complete_or_disabled(event, config.reranking_config.enabled)


@precondition()
async def context_ready_for_history_limit(
    context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
    context_sufficient_event: ContextSufficientAcceptEvent | None = None,
) -> bool:
    """
    Precondition for limit_chat_history_with_context_step.
    Allows the step to run when:
    - ExpertAnswerContextEvent is present (expert flow), OR
    - InOrderNodeCombinerEvent is present AND ContextSufficientAcceptEvent is present (normal RAG flow)
    """
    return check_context_ready_for_history_limit_with_expert(context_event, context_sufficient_event)


@precondition()
async def is_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is a successful answer."""
    return check_is_answer_response(event)


@precondition()
async def is_no_answer_response(event: AgentInTheLoop.response) -> bool:
    """Ensures agent in the loop response is an unsuccessful answer."""
    return check_is_no_answer_response(event)


class ExpertRAGAgent(Agent):
    """
    Implements a Retrieval-Augmented Generation (RAG) Agent with expert escalation.

    The ExpertRAGAgent extends the basic RAG functionality with the ability to consult
    human experts when the retrieved context is insufficient to answer the user's question.

    ### Features
    - Limit chat history to fit input token limits.
    - Condenses chat history into standalone question.
    - Retrieve relevant documents from a knowledge base.
    - Order retrieved nodes for better contextual relevance.
    - Generate responses using an LLM based on the context and retrieved information.
    - Expert escalation when context is insufficient (requires user consent).

    Note: For basic RAG functionality without expert escalation, use RAGAgent instead.
    """

    @step(
        name=LocaleString(en="Limit Chat History"),
        description=LocaleString(en="Truncates incoming chat messages to fit within the configured token limit"),
        icon="iconoir:cut",
    )
    async def limit_chat_history_step(
        self,
        event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
    ) -> LimitChatHistoryEvent:
        return do_limit_chat_history(event.messages, agent_config.number_of_input_tokens)

    @step(
        name=LocaleString(en="Condense Standalone Question"),
        description=LocaleString(en="Condenses the chat history and user query into a standalone question."),
    )
    async def condense_standalone_question_step(
        self,
        event: LimitChatHistoryEvent,
        start_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
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
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
    ) -> InOrderNodeCombinerEvent:
        return await do_order_nodes_by_documents(event, t, agent_config.context_prompt, displayer)

    @step(
        name=LocaleString(en="Context Sufficient Guard"),
        description=LocaleString(en="Guards the context to ensure it is sufficient for generating a response."),
    )
    async def context_sufficient_guard_step(
        self,
        agent_config: ExpertRAGAgentConfig,
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
        context_event: InOrderNodeCombinerEvent | ExpertAnswerContextEvent,
        chat_history_event: LimitChatHistoryEvent,
        _: ContextSufficientAcceptEvent | None,
        start_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        agent_config: ExpertRAGAgentConfig,
    ) -> LimitChatHistoryWithContextEvent:
        return do_limit_chat_history_with_context(
            context_event.context_message,
            chat_history_event.limited_history,
            start_event.last_user_message,
            agent_config.llm.token_counter,
            agent_config.number_of_input_tokens,
        )

    # --- Expert Escalation Steps ---

    @step(
        name=LocaleString(en="Handle Insufficient Context"),
        description=LocaleString(en="Handle insufficient context by asking for expert consent."),
        icon="akar-icons:chat-approve",
    )
    async def insufficient_context_ask_expert_step(
        self,
        _: ContextInsufficientRejectEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.confirmation.request:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.context_not_sufficient"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.asking_for_consent"))
        return HumanInTheLoop.confirmation.invoke(question=t("agent.expert_grounded_agent.messages.consent_question"))

    @step(
        name=LocaleString(en="Consent Answer"),
        description=LocaleString(en="User answered the question for consent."),
        icon="carbon:question-answering",
    )
    async def user_expert_inquiry_response(
        self,
        event: HumanInTheLoop.confirmation.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> UserRequestsExpertEvent | ExpertRejectEvent:
        if event.response is True:
            await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_consented"))
            return UserRequestsExpertEvent()
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.user_declined"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.waiting_for_instructions"))
        return ExpertRejectEvent(reason="User declined expert escalation")

    @step(
        name=LocaleString(en="Invoke ExpertAskingAgent"),
        description=LocaleString(en="Forwarding request to ExpertAskingAgent that will prompt experts."),
        icon="hugeicons:robot-02",
    )
    async def forward_to_expert_asking_agent_step(
        self,
        user_message_event: UserMessageEvent | NamespaceAwareUserMessageEvent,
        _: UserRequestsExpertEvent,
        displayer: EventDisplayer,
        agent_config: ExpertRAGAgentConfig,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.forwarding_to_expert"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_forwarding_confirmation"),
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            "\n",
            model_name=ExpertRAGAgent.__name__,
        )
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_answer_coming_soon"),
            model_name=ExpertRAGAgent.__name__,
        )
        return AgentInTheLoop.invoke(
            agent_class=agent_config.expert_escalation.expert_asking_agent_class,
            agent_id=agent_config.expert_escalation.expert_asking_agent_id,
            start_event=AskExpertStartEvent(
                question_to_expert=user_message_event.user_query,
                locale=user_message_event.locale,
                user=user_message_event.user,
            ),
        )

    @step(
        precondition=is_answer_response,
        name=LocaleString(en="Expert Answer Positive"),
        description=LocaleString(en="ExpertAskingAgent was able to extract information from expert."),
        icon="ix:user-success-filled",
    )
    async def expert_answered_step(
        self,
        displayer: EventDisplayer,
        event: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> ExpertAnswerContextEvent:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_answered"))
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.can_answer_question"))

        # Format the expert conversation as context
        expert_conversation = event.stop_event.expert_conversation
        expert_conversation_text = format_expert_conversation(expert_conversation)

        context_content = t("agent.prompt.expert_context", expert_conversation=expert_conversation_text)
        await displayer.display_thought(f"Expert context: {context_content}")

        context_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=context_content,
        )
        return ExpertAnswerContextEvent(context_message=context_message)

    @step(
        precondition=is_no_answer_response,
        name=LocaleString(en="Expert Answer Negative"),
        description=LocaleString(en="ExpertAskingAgent was NOT able to extract information from expert."),
        icon="ix:user-fail-filled",
    )
    async def expert_not_answered_step(
        self,
        displayer: EventDisplayer,
        _: AgentInTheLoop.response,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(t("agent.expert_grounded_agent.thoughts.expert_unable_to_answer"))
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_unable_to_answer"),
            model_name=ExpertRAGAgent.__name__,
        )
        return StopEvent()

    @step(
        name=LocaleString(en="Expert Answer Error"),
        description=LocaleString(en="ExpertAskingAgent encountered an error."),
        icon="ix:error",
    )
    async def expert_exception_step(
        self,
        displayer: EventDisplayer,
        exception_event: AgentInTheLoop.exception,
        t: LocaleHandler,
    ) -> StopEvent:
        await displayer.display_thought(
            t(
                "agent.expert_grounded_agent.thoughts.expert_error",
                error_code=exception_event.exception_event.http_status_code,
                error_message=exception_event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.expert_grounded_agent.messages.expert_error_occurred"),
            model_name=ExpertRAGAgent.__name__,
        )
        return StopEvent()

    @step(
        name=LocaleString(en="Respond with LLM"),
        description=LocaleString(en="Generates a response using the configured LLM."),
    )
    async def respond_with_llm_step(
        self,
        event: LimitChatHistoryWithContextEvent | FewShotRejectEvent | ExpertRejectEvent,
        limited_history_without_context: LimitChatHistoryEvent,
        agent_config: ExpertRAGAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        return await do_respond_with_llm(
            event,
            limited_history_without_context.limited_history,
            agent_config.context_insufficient_prompt,
            agent_config.system_prompt,
            agent_config.llm,
            displayer,
            t,
        )
