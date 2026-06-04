import asyncio
import logging
from typing import ClassVar

from llama_index.core.prompts import RichPromptTemplate
from mongoengine import DoesNotExist
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    LLMStopEvent,
    MetaAnswerReadyEvent,
    MetaQuestionDetectedEvent,
    NotAMetaQuestionEvent,
    RAGStartEvent,
    StopEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import BucketNamespacePair
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs.namespace_selection_agent_config import (
    NamespaceSelectionAgentConfig,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.events.determine_namespaces_event import (
    DetermineNamespacesEvent,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.events.follow_up_question_hitl import (
    FollowUpQuestionHitl,
    FollowUpQuestionRequestEvent,
    FollowUpQuestionResponseEvent,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.events.namespace_approval_hitl import (
    NamespaceApprovalHitl,
    NamespaceApprovalRequestEvent,
    NamespaceApprovalResponseEvent,
)
from swiss_ai_hub.agent.agents.namespace_selection_agent.llm.namespace_decision import NamespaceDecision
from swiss_ai_hub.agent.agents.namespace_selection_agent.utils import (
    format_approval_question,
    format_available_namespaces,
    format_conversation_history,
    truncate_conversation_history,
    validate_namespace_selection,
)
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.self_awareness.meta_question_gate import check_passed_meta_question_gate
from swiss_ai_hub.agent.self_awareness.meta_question_workflow_summary import summarize_workflow_for_meta_answer
from swiss_ai_hub.agent.self_awareness.self_awareness_step_functions import (
    do_answer_meta_question,
    do_detect_meta_question,
)
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


# RunContext keys
AVAILABLE_NAMESPACES_KEY = "available_namespaces"
CONVERSATION_HISTORY_KEY = "conversation_history"
PROPOSED_NAMESPACES_KEY = "proposed_namespaces"

# ThreadContext keys
NAMESPACE_SELECTION_KEY = "namespace_selection"


@precondition()
async def needs_selection(
    thread_context: ThreadContext,
    start_event: UserMessageEvent,
    clear: NotAMetaQuestionEvent | None = None,
) -> bool:
    """Check if user needs to select namespaces (no existing selection), gated by meta-question detection."""
    if not check_passed_meta_question_gate(start_event, clear):
        return False
    selection = await thread_context.get(NAMESPACE_SELECTION_KEY)
    return selection is None


@precondition()
async def has_selection(
    thread_context: ThreadContext,
    start_event: UserMessageEvent,
    clear: NotAMetaQuestionEvent | None = None,
) -> bool:
    """Check if user already has namespace selection stored, gated by meta-question detection."""
    if not check_passed_meta_question_gate(start_event, clear):
        return False
    selection = await thread_context.get(NAMESPACE_SELECTION_KEY)
    return selection is not None


@precondition()
async def is_namespace_approved(event: NamespaceApprovalResponseEvent) -> bool:
    """Check if user approved the namespace selection."""
    return event.response


@precondition()
async def is_namespace_rejected(event: NamespaceApprovalResponseEvent) -> bool:
    """Check if user rejected the namespace selection."""
    return not event.response


class NamespaceSelectionAgent(Agent):
    """Agent that determines namespaces via LLM-driven conversation and delegates to RAG.

    ### Workflow

    **First message (no selection):**
    1. Fetch available namespaces from configured buckets
    2. Store original query for later forwarding
    3. Enter determination loop: LLM decides if it has enough info
    4. If not enough info: ask follow-up question (HITL), loop back
    5. If enough info: propose namespaces, ask for approval (HITL)
    6. If approved: store selection, forward original query to RAG
    7. If rejected: add rejection to conversation, loop back

    **Subsequent messages (has selection):**
    1. Read selection from ThreadContext
    2. Forward query to RAG agent via AgentInTheLoop with namespace selection
    3. Return RAG response to user
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.namespace_selection_agent.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.namespace_selection_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:book"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.detect.description"),
        icon="mdi:help-circle-outline",
    )
    async def detect_meta_question_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaQuestionDetectedEvent | NotAMetaQuestionEvent:
        """Gate every chat message: classify it as a meta question or release the normal pipeline."""
        return await do_detect_meta_question(
            user_query=event.user_query,
            llm_config=agent_config.llm,
            displayer=displayer,
            t=t,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.answer.description"),
        icon="mdi:account-voice",
    )
    async def answer_meta_question_step(
        self,
        event: MetaQuestionDetectedEvent,
        user_message_event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> MetaAnswerReadyEvent:
        """
        Stream a meta answer from the agent's own identity and workflow, then hand off to a separate
        stop step. The terminal stop event must NOT be emitted here: emitting it back-to-back with the
        answer's chunks lets it race them in the streaming layer and blanks the answer in the chat UI.
        """
        stop_event = await do_answer_meta_question(
            event=event,
            agent_name=t.extract(agent_config.name),
            agent_description=t.extract(agent_config.description),
            workflow_summary=summarize_workflow_for_meta_answer(self.get_steps(), t),
            chat_history=user_message_event.messages,
            llm_config=agent_config.llm,
            displayer=displayer,
            t=t,
        )
        return MetaAnswerReadyEvent(stop_event=stop_event)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.stop.name"),
        description=AgentLocaleString.from_i18n_path("agent.self_awareness.steps.stop.description"),
        icon="mdi:flag-checkered",
    )
    async def stop_after_meta_answer_step(self, event: MetaAnswerReadyEvent) -> LLMStopEvent:
        """Re-emit the streamed answer's stop event as the run's terminal event, a dispatch cycle later."""
        return event.stop_event

    # === First-time flow: No selection exists ===

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.initialize_determination.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.initialize_determination.description"
        ),
        icon="mage:search",
        precondition=needs_selection,
    )
    async def initialize_determination_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> DetermineNamespacesEvent:
        """Fetch namespaces, store original query, and start determination loop."""
        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.fetching_namespaces"))

        available_namespaces: dict[str, list[str]] = {}
        for bucket_name in agent_config.bucket_names:
            try:
                bucket = await asyncio.to_thread(BucketEntity.get_bucket_by_bucket_name, bucket_name)
            except DoesNotExist:
                logger.warning("Bucket '%s' not found - skipping", bucket_name)
                continue

            namespaces = await asyncio.to_thread(NamespaceEntity.get_namespaces_by_bucket, str(bucket.id))
            if not namespaces:
                logger.warning("No namespaces found in bucket '%s' - skipping", bucket_name)
                continue

            available_namespaces[bucket_name] = [ns.namespace_name for ns in namespaces]

        # Store in RunContext
        logger.debug("Available namespaces fetched: %s", available_namespaces)
        await run_context.set(AVAILABLE_NAMESPACES_KEY, available_namespaces)

        conversation_history = [{"role": "user", "content": event.user_query}]
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.starting_determination"))

        return DetermineNamespacesEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.determine_namespaces.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.determine_namespaces.description"
        ),
        icon="mage:light-bulb",
    )
    async def determine_namespaces_step(
        self,
        _: DetermineNamespacesEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> FollowUpQuestionRequestEvent | NamespaceApprovalRequestEvent | DetermineNamespacesEvent:
        """Use LLM to determine if enough info exists to select namespaces."""
        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.analyzing_request"))

        available_namespaces: dict[str, list[str]] = await run_context.get(AVAILABLE_NAMESPACES_KEY, {})
        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])

        # Format namespaces for LLM
        namespaces_str = format_available_namespaces(available_namespaces)
        conversation_str = format_conversation_history(conversation_history)

        logger.debug("Formatted namespaces string:\n%s", namespaces_str)
        logger.debug("Conversation history:\n%s", conversation_str)

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            prompt = RichPromptTemplate(t("agent.namespace_selection_agent.prompts.determination"))
            decision: NamespaceDecision = await llm.astructured_predict(
                NamespaceDecision,
                prompt,
                available_namespaces=namespaces_str,
                conversation_history=conversation_str,
            )

        await displayer.display_thought(
            t("agent.namespace_selection_agent.thoughts.llm_decision", reasoning=decision.reasoning)
        )

        if not decision.has_enough_information:
            # Need more info - ask follow-up question
            question = decision.follow_up_question or t("agent.namespace_selection_agent.messages.default_follow_up")
            return FollowUpQuestionHitl.invoke(question=question)

        # Have enough info - validate and propose namespaces for approval
        selected = decision.selected_namespaces or {}

        if not validate_namespace_selection(selected, available_namespaces):
            logger.error(
                "Invalid namespace selection: %s. Available namespaces: %s",
                selected,
                available_namespaces,
            )
            # Invalid selection - add error to conversation with details and retry
            error_message = t(
                "agent.namespace_selection_agent.messages.invalid_selection",
                selected=selected,
                available_namespaces=available_namespaces,
            )
            conversation_history.append({"role": "system", "content": error_message})
            await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)
            return DetermineNamespacesEvent()

        await run_context.set(PROPOSED_NAMESPACES_KEY, selected)

        approval_question = format_approval_question(selected, agent_config.approval_message_template, t)
        return NamespaceApprovalHitl.invoke(question=approval_question)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.process_follow_up.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.process_follow_up.description"
        ),
        icon="mage:message-dots",
    )
    async def process_follow_up_step(
        self,
        event: FollowUpQuestionResponseEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> DetermineNamespacesEvent:
        """Append user's response to conversation history and loop back."""
        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.processing_follow_up"))

        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])

        conversation_history.append({"role": "assistant", "content": event.request_event.question})
        conversation_history.append({"role": "user", "content": event.response})
        conversation_history = truncate_conversation_history(
            conversation_history, agent_config.max_conversation_history_entries
        )
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        return DetermineNamespacesEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.process_approval_approved.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.process_approval_approved.description"
        ),
        icon="mage:check",
        precondition=is_namespace_approved,
    )
    async def process_approval_approved_step(
        self,
        _: NamespaceApprovalResponseEvent,
        start_event: UserMessageEvent | RAGStartEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request:
        """Store selection and forward to RAG."""
        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.selection_approved"))

        selected: dict[str, str] = await run_context.get(PROPOSED_NAMESPACES_KEY, {})
        await thread_context.set(NAMESPACE_SELECTION_KEY, selected)

        namespace_pairs = [
            BucketNamespacePair(bucket_name=bucket, namespace_name=namespace) for bucket, namespace in selected.items()
        ]

        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.forwarding_to_rag"))

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_delegation.rag_agent.agent_class,
            agent_id=agent_config.rag_delegation.rag_agent.agent_id,
            start_event=RAGStartEvent(
                messages=start_event.messages,
                user=start_event.user,
                locale=start_event.locale,
                files=start_event.files if start_event.files else [],
                selected_namespaces=namespace_pairs,
            ),
            share_thread_id=True,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.process_approval_rejected.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.process_approval_rejected.description"
        ),
        icon="mage:x",
        precondition=is_namespace_rejected,
    )
    async def process_approval_rejected_step(
        self,
        event: NamespaceApprovalResponseEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> DetermineNamespacesEvent:
        """Add rejection to conversation history and loop back to determination."""
        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.selection_rejected"))

        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])
        conversation_history.append({"role": "assistant", "content": event.request_event.question})
        conversation_history.append(
            {
                "role": "user",
                "content": t("agent.namespace_selection_agent.messages.user_rejected_selection"),
            }
        )
        conversation_history = truncate_conversation_history(
            conversation_history, agent_config.max_conversation_history_entries
        )
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        return DetermineNamespacesEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.rag_response.name"),
        description=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.rag_response.description"),
        icon="mage:message",
    )
    async def rag_response_step(
        self,
        event: AgentInTheLoop.response,
    ) -> StopEvent:
        """Pass through RAG response as our stop event."""
        return event.stop_event

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.rag_error.name"),
        description=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.rag_error.description"),
        icon="mage:exclamation-triangle",
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
                "agent.namespace_selection_agent.thoughts.rag_error",
                error_code=event.exception_event.http_status_code,
                error_message=event.exception_event.message,
            )
        )
        await displayer.display_chunk(
            t("agent.namespace_selection_agent.messages.rag_error"),
            model_name=NamespaceSelectionAgent.__name__,
        )
        return StopEvent()

    # === Subsequent messages: Selection exists ===

    @step(
        name=AgentLocaleString.from_i18n_path("agent.namespace_selection_agent.steps.forward_to_rag.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.namespace_selection_agent.steps.forward_to_rag.description"
        ),
        icon="mage:upload",
        precondition=has_selection,
    )
    async def forward_to_rag_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        _clear: NotAMetaQuestionEvent | None = None,
    ) -> AgentInTheLoop.request:
        """Forward message to RAG agent with stored namespace selection."""
        selected: dict[str, str] = await thread_context.get(NAMESPACE_SELECTION_KEY, {})

        await displayer.display_thought(t("agent.namespace_selection_agent.thoughts.forwarding_to_rag"))

        namespace_pairs = [
            BucketNamespacePair(bucket_name=bucket, namespace_name=namespace) for bucket, namespace in selected.items()
        ]

        return AgentInTheLoop.invoke(
            agent_class=agent_config.rag_delegation.rag_agent.agent_class,
            agent_id=agent_config.rag_delegation.rag_agent.agent_id,
            start_event=RAGStartEvent(
                messages=event.messages,
                user=event.user,
                locale=event.locale,
                files=event.files,
                selected_namespaces=namespace_pairs,
            ),
            share_thread_id=True,
        )
