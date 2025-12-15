from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, HumanInTheLoop, StopEvent
from aihub_lib.nats.events.semantic.llm import LLMStopEvent
from aihub_lib.nats.events.user import UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.namespace_data import (
    AVAILABLE_NAMESPACES_KEY,
    NAMESPACE_SELECTIONS_KEY,
    PARTIAL_SELECTIONS_KEY,
    BucketInfo,
    create_rag_event_with_overrides,
    fetch_available_namespaces,
)
from aihub_agent.agents.NamespaceSelectionAgent.namespace_formatting import generate_selection_question
from aihub_agent.agents.NamespaceSelectionAgent.selection_parsing import parse_selection_response
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step


@precondition()
async def has_namespace_selection(thread_context: ThreadContext) -> bool:
    """Precondition: namespace selection already exists in ThreadContext."""
    selections = await thread_context.get(NAMESPACE_SELECTIONS_KEY)
    return selections is not None and len(selections) > 0


@precondition()
async def no_namespace_selection(thread_context: ThreadContext) -> bool:
    """Precondition: no namespace selection exists yet."""
    selections = await thread_context.get(NAMESPACE_SELECTIONS_KEY)
    return selections is None or len(selections) == 0


class NamespaceSelectionAgent(Agent):
    """
    Agent that asks the user which namespace to use for each configured bucket,
    then delegates all messages to the configured RAG agent.

    The selection flow uses chat-style HITL (normal messages, not popups) for a
    conversational experience. Once namespaces are selected, they are stored in
    ThreadContext and all future messages are delegated to the RAG agent with
    namespace overrides.

    ### Workflow

    1. **First message (no selection)**: Fetches namespaces for configured buckets,
       generates a question asking the user to select, and waits for response.

    2. **Selection loop**: Parses user response, asks for clarification if needed,
       until all buckets have a selected namespace.

    3. **Subsequent messages**: Delegates directly to RAG agent with namespace overrides.
    """

    @step(
        name=LocaleString(en="Delegate to RAG"),
        description=LocaleString(en="Delegates the user message to the configured RAG agent with namespace overrides."),
        precondition=has_namespace_selection,
        icon="hugeicons:robot-02",
    )
    async def delegate_to_rag_step(
        self,
        event: UserMessageEvent,
        thread_context: ThreadContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Delegates to RAG agent when namespace selection already exists."""
        selections: dict[str, str] = await thread_context.get(NAMESPACE_SELECTIONS_KEY, {})

        await displayer.display_thought(t("agent.namespace_selection.thoughts.delegating_to_rag"))

        rag_event, _ = create_rag_event_with_overrides(
            event=event,
            selections=selections,
            knowledge_retrieval_agent_id=agent_config.knowledge_retrieval_agent_id,
            rag_agent_class=agent_config.rag_agent.agent_class,
            rag_agent_id=agent_config.rag_agent.agent_id,
        )

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_agent.agent_class,
            agent_id=agent_config.rag_agent.agent_id,
            start_event=rag_event,
        )

    @step(
        name=LocaleString(en="Ask Namespace Selection"),
        description=LocaleString(en="Asks the user which namespace to use for each bucket."),
        precondition=no_namespace_selection,
        icon="mdi:folder-question",
    )
    async def ask_selection_step(
        self,
        event: UserMessageEvent,
        run_context: RunContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> HumanInTheLoop.chat.request:
        """Fetches namespaces and asks user to select."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.fetching_namespaces"))

        available_namespaces = await fetch_available_namespaces(agent_config)
        available_namespaces_serialized = {k: v.model_dump() for k, v in available_namespaces.items()}
        await run_context.set(AVAILABLE_NAMESPACES_KEY, available_namespaces_serialized)
        await run_context.set(PARTIAL_SELECTIONS_KEY, {})

        question = await generate_selection_question(
            available_namespaces=available_namespaces,
            user_query=event.user_query,
            agent_config=agent_config,
            t=t,
            displayer=displayer,
        )

        return HumanInTheLoop.chat.invoke(question)

    @step(
        name=LocaleString(en="Parse Selection"),
        description=LocaleString(en="Parses user response and extracts namespace selections."),
        max_executions_per_run=5,
        icon="mdi:check-circle",
    )
    async def parse_selection_step(
        self,
        event: HumanInTheLoop.chat.response,
        start_event: UserMessageEvent,
        run_context: RunContext,
        thread_context: ThreadContext,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request | HumanInTheLoop.chat.request:
        """Parses user selection and either delegates or asks for clarification."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.parsing_selection"))

        available_namespaces_raw = await run_context.get(AVAILABLE_NAMESPACES_KEY, {})
        available_namespaces: dict[str, BucketInfo] = {
            k: BucketInfo.model_validate(v) for k, v in available_namespaces_raw.items()
        }
        partial_selections: dict[str, str] = await run_context.get(PARTIAL_SELECTIONS_KEY, {})

        result = await parse_selection_response(
            user_response=event.response,
            available_namespaces=available_namespaces,
            partial_selections=partial_selections,
            agent_config=agent_config,
            t=t,
            displayer=displayer,
        )

        if result.complete:
            await thread_context.set(NAMESPACE_SELECTIONS_KEY, result.selections)
            await displayer.display_thought(t("agent.namespace_selection.thoughts.selection_complete"))

            rag_event, _ = create_rag_event_with_overrides(
                event=start_event,
                selections=result.selections,
                knowledge_retrieval_agent_id=agent_config.knowledge_retrieval_agent_id,
                rag_agent_class=agent_config.rag_agent.agent_class,
                rag_agent_id=agent_config.rag_agent.agent_id,
            )

            return AgentInTheLoop.invoke(
                agent_class=agent_config.rag_agent.agent_class,
                agent_id=agent_config.rag_agent.agent_id,
                start_event=rag_event,
            )
        else:
            await run_context.set(PARTIAL_SELECTIONS_KEY, result.selections)
            return HumanInTheLoop.chat.invoke(result.follow_up)

    @step(
        name=LocaleString(en="RAG Response"),
        description=LocaleString(en="Passes through the RAG agent's response."),
        icon="hugeicons:robot-02",
    )
    async def rag_response_step(
        self,
        event: AgentInTheLoop.response,
    ) -> LLMStopEvent:
        """Passes through the RAG agent's response."""
        return event.stop_event

    @step(
        name=LocaleString(en="RAG Error"),
        description=LocaleString(en="Handles errors from the RAG agent."),
        icon="mdi:alert",
    )
    async def rag_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handles errors from the RAG agent."""
        await displayer.display_thought(
            t(
                "agent.namespace_selection.thoughts.rag_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.namespace_selection.messages.rag_error"),
            model_name="NamespaceSelectionAgent",
        )
        return StopEvent()
