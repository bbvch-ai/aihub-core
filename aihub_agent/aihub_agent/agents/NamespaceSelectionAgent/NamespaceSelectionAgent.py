"""
NamespaceSelectionAgent - Orchestrates namespace selection with natural conversation.

This agent:
1. Receives user queries
2. Uses LLM router to detect topic changes (asks user to confirm if topic changed)
3. Uses LLM to select relevant knowledge namespaces
4. Always asks user to approve selection via chat-style HITL
5. Supports correction loops when user wants changes
6. Persists selection in ThreadContext for subsequent queries
7. Delegates to RAGAgent via AgentInTheLoop with RAGWithSourcesStartEvent
"""

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import (
    AgentInTheLoop,
    HumanInTheLoop,
    KnowledgeSource,
    StopEvent,
)
from aihub_lib.nats.events.guard import TopicChangedEvent, TopicUnchangedAcceptEvent
from aihub_lib.nats.events.router.RouterEvent import RouterEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.KeepSourcesEvent import KeepSourcesEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.NamespaceSelectionEvent import NamespaceSelectionEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.SelectionReadyEvent import SelectionReadyEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.SelectNewSourcesEvent import SelectNewSourcesEvent
from aihub_agent.agents.NamespaceSelectionAgent.helpers import (
    AvailableNamespace,
    build_agent_invocation,
    build_rag_start_event,
    detect_topic_change_with_llm,
    fetch_available_namespaces,
    get_current_sources,
    interpret_approval_response,
    normalize_selection,
    route_topic_change_response,
    save_selected_sources,
    select_namespaces,
)
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.step import step

# RunContext keys for ephemeral state
RUN_KEY_CORRECTION_COUNT = "correction_count"
RUN_KEY_CONVERSATION_CONTEXT = "conversation_context"
RUN_KEY_AVAILABLE_NAMESPACES = "available_namespaces"
RUN_KEY_CURRENT_SELECTION = "current_selection"
RUN_KEY_ORIGINAL_QUERY = "original_query"


class NamespaceSelectionAgent(Agent):
    """
    Orchestrates namespace selection with natural chat-style conversation.

    Uses LLM-based topic detection and always requires user approval for
    namespace selection. Supports correction loops and persists selections
    for subsequent queries in the same thread.
    """

    @step(
        name=LocaleString(en="Check Topic Change"),
        description=LocaleString(en="Uses LLM router to detect if the topic has changed"),
        icon="iconoir:search",
    )
    async def topic_change_guard_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RouterEvent | NamespaceSelectionEvent | TopicUnchangedAcceptEvent:
        """
        Entry point: Check if topic changed from previous conversation.

        If no previous selection exists, proceed directly to namespace selection.
        If previous selection exists, use LLM router to determine if topic changed.
        """
        # Initialize run context
        await run_context.set(RUN_KEY_CORRECTION_COUNT, 0)
        await run_context.set(RUN_KEY_CONVERSATION_CONTEXT, [])
        await run_context.set(RUN_KEY_ORIGINAL_QUERY, event.user_query)

        user_query = event.user_query
        await displayer.display_thought(t("agent.namespace_selection.thoughts.starting_selection"))

        # Get current state (from previous query in same thread)
        current_sources = await get_current_sources(thread_context)

        # If no current selection, proceed directly to namespace selection
        if current_sources is None:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.first_query"))
            return NamespaceSelectionEvent(
                selected_sources=[],
                reasoning="First query in thread - need to select namespaces",
            )

        # If topic changes are disabled, skip guard and reuse sources directly
        if not agent_config.allow_topic_change:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.reusing_selection"))
            return TopicUnchangedAcceptEvent(
                current_sources=current_sources,
                reason="Topic change detection disabled - reusing previous selection",
            )

        # Use LLM router to detect topic change using the message history
        async with agent_config.selection_llm.cost_reporting_llm(displayer) as llm:
            router_event = await detect_topic_change_with_llm(
                current_query=user_query,
                current_sources=current_sources,
                llm=llm,
                displayer=displayer,
                t=t,
                previous_messages=event.messages,
            )

        return router_event

    @step(
        name=LocaleString(en="Ask About Topic Change"),
        description=LocaleString(en="Asks user if they want to search different sources"),
        icon="iconoir:chat-bubble-question",
    )
    async def ask_topic_change_step(
        self,
        event: TopicChangedEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.chat.request:
        """
        When topic change is detected, ask user if they want different sources.
        """
        sources_str = ", ".join(s.display_name or s.namespace_name for s in event.current_sources)

        question = t(
            "agent.namespace_selection.messages.topic_change_question",
            sources=sources_str,
        )

        await displayer.display_thought(t("agent.namespace_selection.thoughts.asking_topic_change"))
        return HumanInTheLoop.chat.invoke(question=question)

    @step(
        name=LocaleString(en="Handle Topic Response"),
        description=LocaleString(en="Interprets user's response about topic change"),
        icon="iconoir:check",
    )
    async def handle_topic_response_step(
        self,
        event: HumanInTheLoop.chat.response,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> RouterEvent:
        """
        Interpret user's response to topic change question using router pattern.
        """
        current_sources = await get_current_sources(thread_context) or []

        async with agent_config.selection_llm.cost_reporting_llm(displayer) as llm:
            router_event = await route_topic_change_response(
                llm=llm,
                t=t,
                user_response=event.response,
                current_sources=current_sources,
            )

        # Display thought based on selected route
        if isinstance(router_event.selected_option.event, KeepSourcesEvent):
            await displayer.display_thought(t("agent.namespace_selection.thoughts.user_keeps_sources"))
        else:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.user_wants_new_sources"))

        return router_event

    @step(
        name=LocaleString(en="Reuse Current Sources"),
        description=LocaleString(en="Skips selection when topic is unchanged"),
        icon="iconoir:arrow-right",
    )
    async def reuse_sources_step(
        self,
        event: TopicUnchangedAcceptEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> SelectionReadyEvent:
        """
        When topic is unchanged, reuse current sources without asking.
        """
        await displayer.display_thought(t("agent.namespace_selection.thoughts.reusing_selection"))
        return SelectionReadyEvent(
            selected_sources=event.current_sources,
            reasoning="Topic unchanged - reusing current selection",
        )

    @step(
        name=LocaleString(en="Select Namespaces"),
        description=LocaleString(en="Uses LLM to select relevant knowledge namespaces"),
        icon="iconoir:search",
    )
    async def select_namespaces_step(
        self,
        event: NamespaceSelectionEvent | SelectNewSourcesEvent,
        start_event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> NamespaceSelectionEvent:
        """
        Perform LLM-based namespace selection.
        """
        await displayer.display_thought(t("agent.namespace_selection.thoughts.selecting_namespaces"))

        # Fetch available namespaces
        bucket_names = [b.bucket_name for b in agent_config.allowed_buckets]
        available_namespaces = fetch_available_namespaces(bucket_names, start_event.locale)
        await run_context.set(RUN_KEY_AVAILABLE_NAMESPACES, [ns.model_dump() for ns in available_namespaces])

        if not available_namespaces:
            return NamespaceSelectionEvent(
                selected_sources=[],
                reasoning="No namespaces available in configured buckets",
            )

        # Get correction context if any
        conversation_context = await run_context.get(RUN_KEY_CONVERSATION_CONTEXT, [])

        # Include user preference if coming from topic change
        user_preference = None
        if isinstance(event, SelectNewSourcesEvent) and event.user_preference:
            user_preference = event.user_preference

        result = await select_namespaces(
            start_event.user_query,
            available_namespaces,
            agent_config.selection_llm,
            displayer,
            t,
            selection_system_prompt=agent_config.selection_system_prompt,
            conversation_context=conversation_context,
            user_correction=user_preference,
        )

        # Normalize: exactly one namespace per allowed bucket
        selected_sources = normalize_selection(
            result.selected_sources,
            available_namespaces,
            bucket_names,
        )

        await run_context.set(RUN_KEY_CURRENT_SELECTION, [s.model_dump() for s in selected_sources])

        return NamespaceSelectionEvent(
            selected_sources=selected_sources,
            reasoning=result.reasoning,
        )

    @step(
        name=LocaleString(en="Request Approval"),
        description=LocaleString(en="Asks user to approve the namespace selection"),
        icon="iconoir:chat-bubble-question",
    )
    async def request_approval_step(
        self,
        event: NamespaceSelectionEvent,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.chat.request:
        """
        Always ask user to approve the namespace selection via chat.
        """
        sources_str = ", ".join(s.display_name or s.namespace_name for s in event.selected_sources)

        question = t(
            "agent.namespace_selection.messages.approval_question",
            sources=sources_str,
        )

        await displayer.display_thought(t("agent.namespace_selection.thoughts.requesting_approval"))
        return HumanInTheLoop.chat.invoke(question=question)

    @step(
        name=LocaleString(en="Process Approval"),
        description=LocaleString(en="Interprets user's approval response"),
        icon="iconoir:check",
    )
    async def process_approval_step(
        self,
        event: HumanInTheLoop.chat.response,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> SelectionReadyEvent | NamespaceSelectionEvent:
        """
        Interpret user's approval response and decide next action.
        """
        correction_count = await run_context.get(RUN_KEY_CORRECTION_COUNT, 0)
        current_selection_data = await run_context.get(RUN_KEY_CURRENT_SELECTION, [])
        current_selection = [KnowledgeSource(**s) for s in current_selection_data]
        available_ns_data = await run_context.get(RUN_KEY_AVAILABLE_NAMESPACES, [])
        available_namespaces = [AvailableNamespace(**ns) for ns in available_ns_data]

        # Use LLM to interpret the response
        async with agent_config.selection_llm.cost_reporting_llm(displayer) as llm:
            interpretation = await interpret_approval_response(
                user_response=event.response,
                current_selection=current_selection,
                available_namespaces=available_namespaces,
                llm=llm,
                t=t,
                correction_prompt=agent_config.correction_prompt,
            )

        if interpretation.intent == "approve":
            await displayer.display_thought(t("agent.namespace_selection.thoughts.user_approved"))
            return SelectionReadyEvent(
                selected_sources=current_selection,
                reasoning="User approved selection",
            )

        # Check if max corrections reached
        if correction_count >= agent_config.max_correction_rounds:
            await displayer.display_thought(t("agent.namespace_selection.thoughts.max_corrections_reached"))
            return SelectionReadyEvent(
                selected_sources=current_selection,
                reasoning=f"Max correction rounds ({agent_config.max_correction_rounds}) reached",
            )

        # User rejected or corrected - loop back
        await run_context.set(RUN_KEY_CORRECTION_COUNT, correction_count + 1)

        # Add correction context
        conversation_context = await run_context.get(RUN_KEY_CONVERSATION_CONTEXT, [])
        conversation_context.append(f"User feedback: {event.response}")
        if interpretation.correction_details:
            conversation_context.append(f"Correction: {interpretation.correction_details}")
        await run_context.set(RUN_KEY_CONVERSATION_CONTEXT, conversation_context)

        await displayer.display_thought(t("agent.namespace_selection.thoughts.reselecting", feedback=event.response))

        # Return NamespaceSelectionEvent to trigger re-selection
        # This will be processed by select_namespaces_step again
        return NamespaceSelectionEvent(
            selected_sources=current_selection,
            reasoning=f"User correction: {interpretation.correction_details or event.response}",
        )

    @step(
        name=LocaleString(en="Invoke RAG Agent"),
        description=LocaleString(en="Delegates to RAGAgent with selected knowledge sources"),
        icon="iconoir:brain",
    )
    async def invoke_rag_step(
        self,
        event: SelectionReadyEvent | KeepSourcesEvent,
        start_event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """
        Stores selection in ThreadContext and invokes RAGAgent with selected sources.
        """
        # Get sources from the event
        if isinstance(event, SelectionReadyEvent):
            selected_sources = event.selected_sources
            reasoning = event.reasoning
        else:  # KeepSourcesEvent
            selected_sources = event.current_sources
            reasoning = event.reasoning

        # Persist selection for future queries
        await save_selected_sources(thread_context, selected_sources)

        await displayer.display_thought(
            t(
                "agent.namespace_selection.thoughts.invoking_rag",
                sources=", ".join([s.display_name or s.namespace_name for s in selected_sources]),
            )
        )

        # Build and invoke RAG agent
        rag_start_event = build_rag_start_event(start_event, selected_sources, reasoning)
        return build_agent_invocation(
            agent_config.rag_agent_class,
            agent_config.rag_agent_id,
            rag_start_event,
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
    ) -> StopEvent:
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
