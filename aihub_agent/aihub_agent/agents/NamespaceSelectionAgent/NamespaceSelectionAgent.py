import re

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, StopEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.NamespaceSelectionHitl import (
    NamespaceSelectionHitl,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.SelectionStoredEvent import SelectionStoredEvent
from aihub_agent.agents.RagAgent.events.BucketNamespacePair import BucketNamespacePair
from aihub_agent.agents.RagAgent.events.NamespaceAwareStartEvent import NamespaceAwareStartEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step

NAMESPACE_SELECTION_KEY = "namespace_selection"
AVAILABLE_NAMESPACES_KEY = "available_namespaces"


@precondition()
async def needs_selection(thread_context: ThreadContext) -> bool:
    """Check if user needs to select namespaces (no existing selection)."""
    selection = await thread_context.get(NAMESPACE_SELECTION_KEY)
    return selection is None


@precondition()
async def has_selection(thread_context: ThreadContext) -> bool:
    """Check if user already has namespace selection stored."""
    selection = await thread_context.get(NAMESPACE_SELECTION_KEY)
    return selection is not None


class NamespaceSelectionAgent(Agent):
    """
    Agent that prompts users to select namespaces on first interaction and
    delegates subsequent queries to a configured RAG agent.

    ### Workflow

    **First message (no selection):**
    1. Fetch available namespaces from configured buckets
    2. Ask user to select one namespace per bucket (HITL)
    3. Store selection in ThreadContext
    4. Confirm selection to user

    **Subsequent messages (has selection):**
    1. Read selection from ThreadContext
    2. Forward query to RAG agent via AgentInTheLoop with namespace selection
    3. Return RAG response to user

    ### Features
    - Configurable bucket list
    - Persistent namespace selection per conversation thread
    - Integration with RAGAgent via AITL
    """

    # === First-time flow: No selection exists ===

    @step(
        name=LocaleString(en="Fetch Namespaces"),
        description=LocaleString(en="Fetches available namespaces from configured buckets"),
        icon="tabler:folder-search",
        precondition=needs_selection,
    )
    async def fetch_namespaces_step(
        self,
        _: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> NamespaceSelectionHitl.request:
        """Fetch namespaces from configured buckets and ask user to select."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.fetching_namespaces"))

        available_namespaces: dict[str, list[str]] = {}
        for bucket_name in agent_config.bucket_names:
            bucket = BucketEntity.get_bucket_by_bucket_name(bucket_name)
            namespaces = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))
            available_namespaces[bucket_name] = [ns.namespace_name for ns in namespaces]

        # Store in RunContext for retrieval in process_selection_step
        await run_context.set(AVAILABLE_NAMESPACES_KEY, available_namespaces)

        question = _format_selection_question(available_namespaces, agent_config.selection_prompt, t)
        return NamespaceSelectionHitl.invoke(question=question)

    @step(
        name=LocaleString(en="Process Selection"),
        description=LocaleString(en="Processes user's namespace selection and stores it"),
        icon="tabler:check",
    )
    async def process_selection_step(
        self,
        event: NamespaceSelectionHitl.response,
        run_context: RunContext,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> SelectionStoredEvent:
        """Parse user's selection, validate, and store in ThreadContext."""
        available: dict[str, list[str]] = await run_context.get(AVAILABLE_NAMESPACES_KEY, {})
        user_response = event.response

        await displayer.display_thought(t("agent.namespace_selection.thoughts.processing_selection"))

        selected = _parse_namespace_selection(user_response, available)

        if not _validate_selection(selected, available):
            await displayer.display_thought(t("agent.namespace_selection.thoughts.invalid_selection"))
            selected = _get_default_selection(available)
            await displayer.display_thought(t("agent.namespace_selection.thoughts.using_defaults"))

        await thread_context.set(NAMESPACE_SELECTION_KEY, selected)
        await displayer.display_thought(t("agent.namespace_selection.thoughts.selection_stored"))

        return SelectionStoredEvent(selected_namespaces=selected)

    @step(
        name=LocaleString(en="Confirm Selection"),
        description=LocaleString(en="Confirms namespace selection to user"),
        icon="tabler:message-check",
    )
    async def confirm_selection_step(
        self,
        event: SelectionStoredEvent,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Confirm the selection to user and wait for their next message."""
        selection_summary = _format_selection_summary(event.selected_namespaces, t)
        confirmation_message = f"{t.extract(agent_config.selection_confirmed_message)}\n\n{selection_summary}"
        await displayer.display_chunk(confirmation_message, model_name=NamespaceSelectionAgent.__name__)
        return StopEvent()

    # === Subsequent messages: Selection exists ===

    @step(
        name=LocaleString(en="Forward to RAG"),
        description=LocaleString(en="Forwards query to RAG agent with namespace selection"),
        icon="tabler:send",
        precondition=has_selection,
    )
    async def forward_to_rag_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Forward message to RAG agent with stored namespace selection."""
        selected: dict[str, str] = await thread_context.get(NAMESPACE_SELECTION_KEY, {})

        await displayer.display_thought(t("agent.namespace_selection.thoughts.forwarding_to_rag"))

        # Convert dict to list of BucketNamespacePair
        namespace_pairs = [
            BucketNamespacePair(bucket_name=bucket, namespace_name=namespace) for bucket, namespace in selected.items()
        ]

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_delegation.rag_agent_class,
            agent_id=agent_config.rag_delegation.rag_agent_id,
            start_event=NamespaceAwareStartEvent(
                messages=event.messages,
                user=event.user,
                locale=event.locale,
                files=event.files,
                selected_namespaces=namespace_pairs,
            ),
            share_thread_id=True,
        )

    @step(
        name=LocaleString(en="RAG Response"),
        description=LocaleString(en="Handles response from RAG agent"),
        icon="tabler:message-reply",
    )
    async def rag_response_step(
        self,
        event: AgentInTheLoop.response,
    ) -> StopEvent:
        """Pass through RAG response as our stop event."""
        return event.stop_event

    @step(
        name=LocaleString(en="RAG Error"),
        description=LocaleString(en="Handles error from RAG agent"),
        icon="tabler:alert-triangle",
    )
    async def rag_exception_step(
        self,
        event: AgentInTheLoop.exception,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> StopEvent:
        """Handle RAG agent errors gracefully."""
        await displayer.display_thought(
            t(
                "agent.namespace_selection.thoughts.rag_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.namespace_selection.messages.rag_error"),
            model_name=NamespaceSelectionAgent.__name__,
        )
        return StopEvent()


def _format_selection_question(
    available_namespaces: dict[str, list[str]],
    selection_prompt: LocaleString,
    t: LocaleHandler,
) -> str:
    """Format the namespace selection question for the user."""
    lines = [t.extract(selection_prompt), ""]

    for i, (bucket_name, namespaces) in enumerate(available_namespaces.items(), 1):
        lines.append(f"**{bucket_name}:**")
        for j, ns in enumerate(namespaces, 1):
            lines.append(f"  {j}. {ns}")
        lines.append("")

    lines.append(t("agent.namespace_selection.messages.selection_instruction"))

    return "\n".join(lines)


def _parse_namespace_selection(
    user_response: str,
    available_namespaces: dict[str, list[str]],
) -> dict[str, str]:
    """Parse user's free-text response to extract namespace selection.

    Supports formats like:
    - "1, 2" (numbered selection in order of buckets)
    - "namespace1, namespace2" (direct namespace names)
    - "bucket1: namespace1, bucket2: namespace2" (explicit bucket mapping)
    """
    selected: dict[str, str] = {}
    buckets = list(available_namespaces.keys())

    user_response_lower = user_response.lower().strip()

    for bucket_name, namespaces in available_namespaces.items():
        for ns in namespaces:
            if ns.lower() in user_response_lower:
                selected[bucket_name] = ns
                break

    if len(selected) == len(buckets):
        return selected

    numbers = re.findall(r"\d+", user_response)
    if numbers:
        for i, num_str in enumerate(numbers):
            if i >= len(buckets):
                break
            bucket_name = buckets[i]
            num = int(num_str)
            namespaces = available_namespaces[bucket_name]
            if 1 <= num <= len(namespaces):
                selected[bucket_name] = namespaces[num - 1]

    return selected


def _validate_selection(
    selected: dict[str, str],
    available_namespaces: dict[str, list[str]],
) -> bool:
    """Validate that exactly one namespace is selected per bucket."""
    if set(selected.keys()) != set(available_namespaces.keys()):
        return False

    for bucket_name, namespace in selected.items():
        if namespace not in available_namespaces.get(bucket_name, []):
            return False

    return True


def _get_default_selection(available_namespaces: dict[str, list[str]]) -> dict[str, str]:
    """Get default selection (first namespace from each bucket)."""
    return {bucket: namespaces[0] for bucket, namespaces in available_namespaces.items() if namespaces}


def _format_selection_summary(selected: dict[str, str], t: LocaleHandler) -> str:
    """Format a summary of the selected namespaces."""
    lines = [t("agent.namespace_selection.messages.selection_summary")]
    for bucket, namespace in selected.items():
        lines.append(f"- **{bucket}**: {namespace}")
    return "\n".join(lines)
