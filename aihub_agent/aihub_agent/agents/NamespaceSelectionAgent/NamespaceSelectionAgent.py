"""
NamespaceSelectionAgent - Orchestrates namespace selection before delegating to RAGAgent.

This agent:
1. Receives user queries
2. Uses LLM to select relevant knowledge namespaces
3. Supports clarification loops when selection is uncertain
4. Persists selection in ThreadContext for subsequent queries
5. Detects topic changes and re-evaluates namespace selection
6. Delegates to RAGAgent via AgentInTheLoop with RAGWithSourcesStartEvent
"""

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    HumanInTheLoop,
    KnowledgeSource,
    RAGWithSourcesStartEvent,
    StopEvent,
)
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.ClarificationNeededEvent import ClarificationNeededEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.NamespaceSelectionEvent import NamespaceSelectionEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.SelectionReadyEvent import SelectionReadyEvent
from aihub_agent.agents.NamespaceSelectionAgent.helpers.namespace_selector import (
    AvailableNamespace,
    fetch_available_namespaces,
    select_namespaces,
)
from aihub_agent.agents.NamespaceSelectionAgent.helpers.topic_change_detector import detect_topic_change
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.step import step

# ThreadContext keys for persisted state
THREAD_KEY_SELECTED_SOURCES = "namespace_selection:selected_sources"
THREAD_KEY_QUERY_EMBEDDING = "namespace_selection:query_embedding"

# RunContext keys for ephemeral state
RUN_KEY_CLARIFICATION_COUNT = "clarification_count"
RUN_KEY_CONVERSATION_CONTEXT = "conversation_context"
RUN_KEY_AVAILABLE_NAMESPACES = "available_namespaces"


class NamespaceSelectionAgent(Agent):
    """
    Orchestrates namespace selection before delegating to RAGAgent.

    Uses LLM-based analysis to select relevant namespaces from configured buckets.
    Supports clarification loops when selection confidence is low, and persists
    selections for subsequent queries in the same thread.
    """

    @step(
        name=LocaleString(en="Analyze Query & Select Namespaces"),
        description=LocaleString(en="Analyzes user query and selects relevant knowledge namespaces"),
        icon="iconoir:search",
    )
    async def fetch_and_select_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> NamespaceSelectionEvent:
        """
        Fetches available namespaces, checks for topic changes, and performs LLM-based selection.
        """
        # Initialize run context
        await run_context.set(RUN_KEY_CLARIFICATION_COUNT, 0)
        await run_context.set(RUN_KEY_CONVERSATION_CONTEXT, [])

        user_query = event.user_query
        await displayer.display_thought(t("agent.namespace_selection.thoughts.starting_selection"))

        # Check for topic change and previous selection
        previous_sources = await thread_context.get(THREAD_KEY_SELECTED_SOURCES)
        previous_embedding = await thread_context.get(THREAD_KEY_QUERY_EMBEDDING)

        topic_changed, current_embedding = await detect_topic_change(
            user_query,
            previous_embedding,
            agent_config.embed_model,
            agent_config.auto_switch_threshold,
        )

        # Store current embedding for future comparisons
        await thread_context.set(THREAD_KEY_QUERY_EMBEDDING, current_embedding)

        # If topic hasn't changed and we have previous selection, reuse it
        if not topic_changed and previous_sources:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.reusing_selection"))
            sources = [KnowledgeSource(**s) for s in previous_sources]
            return NamespaceSelectionEvent(
                selected_sources=sources,
                confidence=1.0,
                reasoning="Reusing previous selection - topic unchanged",
                requires_clarification=False,
            )

        if topic_changed:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.topic_changed"))

        # Fetch available namespaces
        bucket_names = [b.bucket_name for b in agent_config.allowed_buckets]
        available_namespaces = fetch_available_namespaces(bucket_names, event.locale)
        await run_context.set(RUN_KEY_AVAILABLE_NAMESPACES, [ns.model_dump() for ns in available_namespaces])

        if not available_namespaces:
            return NamespaceSelectionEvent(
                selected_sources=[],
                confidence=0.0,
                reasoning="No namespaces available in configured buckets",
                requires_clarification=False,
            )

        # Perform LLM-based selection
        result = await select_namespaces(
            user_query,
            available_namespaces,
            agent_config.selection_llm,
            displayer,
            t,
        )

        requires_clarification = result.confidence < agent_config.confidence_threshold
        return NamespaceSelectionEvent(
            selected_sources=result.selected_sources,
            confidence=result.confidence,
            reasoning=result.reasoning,
            requires_clarification=requires_clarification,
        )

    @step(
        name=LocaleString(en="Evaluate Selection"),
        description=LocaleString(en="Decides whether to proceed or request clarification"),
        icon="iconoir:question-mark",
    )
    async def evaluate_selection_step(
        self,
        event: NamespaceSelectionEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> SelectionReadyEvent | ClarificationNeededEvent:
        """
        Decision point: proceed to RAG or enter clarification loop.
        """
        clarification_count = await run_context.get(RUN_KEY_CLARIFICATION_COUNT, 0)

        # Exit loop if confident or max rounds reached
        if event.confidence >= agent_config.confidence_threshold:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.confident_selection"))
            return SelectionReadyEvent(
                selected_sources=event.selected_sources,
                reasoning=event.reasoning,
            )

        if clarification_count >= agent_config.max_clarification_rounds:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.max_rounds_reached"))
            max_rounds = agent_config.max_clarification_rounds
            return SelectionReadyEvent(
                selected_sources=event.selected_sources,
                reasoning=f"Max clarification rounds ({max_rounds}) reached. {event.reasoning}",
            )

        # Need more clarification
        await displayer.display_thought(t("agent.namespace_selection.thoughts.need_clarification"))
        return ClarificationNeededEvent(
            current_sources=event.selected_sources,
            clarification_question=t(
                "agent.namespace_selection.messages.clarification_question",
                sources=", ".join([s.display_name or s.namespace_name for s in event.selected_sources]),
            ),
        )

    @step(
        name=LocaleString(en="Request Clarification"),
        description=LocaleString(en="Asks user for clarification about knowledge sources"),
        icon="iconoir:chat-bubble-question",
    )
    async def request_clarification_step(
        self,
        event: ClarificationNeededEvent,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.input.request:
        """
        Asks the user a clarifying question to help narrow down namespace selection.
        """
        clarification_count = await run_context.get(RUN_KEY_CLARIFICATION_COUNT, 0)
        await run_context.set(RUN_KEY_CLARIFICATION_COUNT, clarification_count + 1)

        await displayer.display_thought(
            t("agent.namespace_selection.thoughts.asking_clarification", round=clarification_count + 1)
        )

        return HumanInTheLoop.input.invoke(question=event.clarification_question)

    @step(
        name=LocaleString(en="Process Clarification Response"),
        description=LocaleString(en="Re-evaluates namespace selection with user's clarification"),
        icon="iconoir:refresh",
    )
    async def process_clarification_step(
        self,
        event: HumanInTheLoop.input.response,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> NamespaceSelectionEvent:
        """
        Re-evaluates namespace selection incorporating user's clarification.
        """
        user_response = event.response
        await displayer.display_thought(
            t("agent.namespace_selection.thoughts.processing_response", response=user_response)
        )

        # Add to conversation context
        conversation_context = await run_context.get(RUN_KEY_CONVERSATION_CONTEXT, [])
        conversation_context.append(f"Q: {event.request_event.question}")
        conversation_context.append(f"A: {user_response}")
        await run_context.set(RUN_KEY_CONVERSATION_CONTEXT, conversation_context)

        # Get available namespaces from run context
        available_ns_data = await run_context.get(RUN_KEY_AVAILABLE_NAMESPACES, [])
        available_namespaces = [AvailableNamespace(**ns) for ns in available_ns_data]

        # Re-run selection with conversation context
        result = await select_namespaces(
            user_response,
            available_namespaces,
            agent_config.selection_llm,
            displayer,
            t,
            conversation_context=conversation_context,
        )

        requires_clarification = result.confidence < agent_config.confidence_threshold
        return NamespaceSelectionEvent(
            selected_sources=result.selected_sources,
            confidence=result.confidence,
            reasoning=result.reasoning,
            requires_clarification=requires_clarification,
        )

    @step(
        name=LocaleString(en="Invoke RAG Agent"),
        description=LocaleString(en="Delegates to RAGAgent with selected knowledge sources"),
        icon="iconoir:brain",
    )
    async def invoke_rag_step(
        self,
        event: SelectionReadyEvent,
        start_event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """
        Stores selection in ThreadContext and invokes RAGAgent with selected sources.
        """
        # Persist selection for future queries
        if agent_config.remember_selection:
            sources_data = [s.model_dump() for s in event.selected_sources]
            await thread_context.set(THREAD_KEY_SELECTED_SOURCES, sources_data)

        await displayer.display_thought(
            t(
                "agent.namespace_selection.thoughts.invoking_rag",
                sources=", ".join([s.display_name or s.namespace_name for s in event.selected_sources]),
            )
        )

        # Build RAGWithSourcesStartEvent
        rag_start_event = RAGWithSourcesStartEvent(
            locale=start_event.locale,
            user=start_event.user,
            messages=start_event.messages,
            files=start_event.files,
            knowledge_sources=event.selected_sources,
            selection_reasoning=event.reasoning,
        )

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_agent_class,
            agent_id=agent_config.rag_agent_id,
            start_event=rag_start_event,
        )

    @step(
        name=LocaleString(en="Forward RAG Response"),
        description=LocaleString(en="Forwards the RAG agent's response to the user"),
        icon="iconoir:forward",
    )
    async def forward_response_step(
        self,
        event: AgentInTheLoop.response,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> LLMStopEvent:
        """
        Forwards the RAGAgent's response.
        """
        await displayer.display_thought(t("agent.namespace_selection.thoughts.forwarding_response"))
        return event.stop_event

    @step(
        name=LocaleString(en="Handle RAG Error"),
        description=LocaleString(en="Handles errors from the RAG agent"),
        icon="iconoir:warning-triangle",
    )
    async def handle_error_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """
        Handles errors from RAGAgent.
        """
        error_msg = t(
            "agent.namespace_selection.messages.rag_error",
            error=event.exception_event.message,
        )
        await displayer.display_thought(error_msg)
        await displayer.display_chunk(error_msg, model_name=NamespaceSelectionAgent.__name__)
        return StopEvent()
