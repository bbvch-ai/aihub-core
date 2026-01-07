import asyncio
import logging

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.generative_ai.retrievers.BucketNamespacePair import BucketNamespacePair
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import AgentInTheLoop, StopEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.prompts import RichPromptTemplate
from mongoengine import DoesNotExist

from aihub_agent.agents.Agent import Agent
from aihub_agent.agents.NamespaceSelectionAgent.configs.NamespaceSelectionAgentConfig import (
    NamespaceSelectionAgentConfig,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.DetermineNamespacesEvent import DetermineNamespacesEvent
from aihub_agent.agents.NamespaceSelectionAgent.events.FollowUpQuestionHitl import (
    FollowUpQuestionHitl,
    FollowUpQuestionRequestEvent,
    FollowUpQuestionResponseEvent,
)
from aihub_agent.agents.NamespaceSelectionAgent.events.NamespaceApprovalHitl import (
    NamespaceApprovalHitl,
    NamespaceApprovalRequestEvent,
    NamespaceApprovalResponseEvent,
)
from aihub_agent.agents.NamespaceSelectionAgent.llm.NamespaceDecision import NamespaceDecision
from aihub_agent.agents.NamespaceSelectionAgent.utils import (
    format_approval_question,
    format_available_namespaces,
    format_conversation_history,
    validate_namespace_selection,
)
from aihub_agent.agents.RagAgent.events.NamespaceAwareStartEvent import NamespaceAwareStartEvent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.context.thread.ThreadContext import ThreadContext
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


# RunContext keys
AVAILABLE_NAMESPACES_KEY = "available_namespaces"
CONVERSATION_HISTORY_KEY = "conversation_history"
ORIGINAL_MESSAGES_KEY = "original_messages"
ORIGINAL_USER_KEY = "original_user"
ORIGINAL_LOCALE_KEY = "original_locale"
ORIGINAL_FILES_KEY = "original_files"
PROPOSED_NAMESPACES_KEY = "proposed_namespaces"

# ThreadContext keys
NAMESPACE_SELECTION_KEY = "namespace_selection"


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

    # === First-time flow: No selection exists ===

    @step(
        name=LocaleString(en="Initialize Namespace Determination"),
        description=LocaleString(en="Fetches namespaces and initializes the determination loop"),
        icon="tabler:folder-search",
        precondition=needs_selection,
    )
    async def initialize_determination_step(
        self,
        event: UserMessageEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> DetermineNamespacesEvent:
        """Fetch namespaces, store original query, and start determination loop."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.fetching_namespaces"))

        # Fetch available namespaces
        available_namespaces: dict[str, list[str]] = {}
        for bucket_name in agent_config.bucket_names:
            try:
                bucket = await asyncio.to_thread(BucketEntity.get_bucket_by_bucket_name, bucket_name)
            except DoesNotExist:
                logger.warning(f"Bucket '{bucket_name}' not found - skipping")
                continue

            namespaces = await asyncio.to_thread(NamespaceEntity.get_namespaces_by_bucket, str(bucket.id))
            if not namespaces:
                logger.warning(f"No namespaces found in bucket '{bucket_name}' - skipping")
                continue

            available_namespaces[bucket_name] = [ns.namespace_name for ns in namespaces]

        # Store in RunContext
        logger.debug(f"Available namespaces fetched: {available_namespaces}")
        await run_context.set(AVAILABLE_NAMESPACES_KEY, available_namespaces)
        await run_context.set(ORIGINAL_MESSAGES_KEY, [msg.model_dump() for msg in event.messages])
        await run_context.set(ORIGINAL_USER_KEY, event.user.model_dump() if event.user else None)
        await run_context.set(ORIGINAL_LOCALE_KEY, event.locale)
        await run_context.set(ORIGINAL_FILES_KEY, [f.model_dump() for f in event.files] if event.files else [])

        # Initialize conversation history with user's first message
        conversation_history = [{"role": "user", "content": event.user_query}]
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        await displayer.display_thought(t("agent.namespace_selection.thoughts.starting_determination"))

        return DetermineNamespacesEvent()

    @step(
        name=LocaleString(en="Determine Namespaces"),
        description=LocaleString(en="LLM analyzes conversation to determine namespaces"),
        icon="tabler:brain",
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
        await displayer.display_thought(t("agent.namespace_selection.thoughts.analyzing_request"))

        available_namespaces: dict[str, list[str]] = await run_context.get(AVAILABLE_NAMESPACES_KEY, {})
        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])

        # Format namespaces for LLM
        namespaces_str = format_available_namespaces(available_namespaces)
        conversation_str = format_conversation_history(conversation_history)

        logger.debug(f"Formatted namespaces string:\n{namespaces_str}")
        logger.debug(f"Conversation history:\n{conversation_str}")

        async with agent_config.llm.cost_reporting_llm(displayer) as llm:
            prompt = RichPromptTemplate(t("agent.namespace_selection.prompts.determination"))
            decision: NamespaceDecision = await llm.astructured_predict(
                NamespaceDecision,
                prompt,
                available_namespaces=namespaces_str,
                conversation_history=conversation_str,
            )

        await displayer.display_thought(
            t("agent.namespace_selection.thoughts.llm_decision", reasoning=decision.reasoning)
        )

        if not decision.has_enough_information:
            # Need more info - ask follow-up question
            question = decision.follow_up_question or t("agent.namespace_selection.messages.default_follow_up")
            return FollowUpQuestionHitl.invoke(question=question)

        # Have enough info - validate and propose namespaces for approval
        selected = decision.selected_namespaces or {}

        if not validate_namespace_selection(selected, available_namespaces):
            # Invalid selection - add error to conversation and retry
            conversation_history.append(
                {
                    "role": "system",
                    "content": "Your selection was invalid. Please select only from the available namespaces listed.",
                }
            )
            await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)
            return DetermineNamespacesEvent()

        await run_context.set(PROPOSED_NAMESPACES_KEY, selected)

        approval_question = format_approval_question(selected, agent_config.approval_message_template, t)
        return NamespaceApprovalHitl.invoke(question=approval_question)

    @step(
        name=LocaleString(en="Process Follow-Up"),
        description=LocaleString(en="Processes user's follow-up response and continues determination"),
        icon="tabler:message-dots",
    )
    async def process_follow_up_step(
        self,
        event: FollowUpQuestionResponseEvent,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> DetermineNamespacesEvent:
        """Append user's response to conversation history and loop back."""
        await displayer.display_thought(t("agent.namespace_selection.thoughts.processing_follow_up"))

        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])

        # Add the question that was asked and the user's response
        conversation_history.append({"role": "assistant", "content": event.request_event.question})
        conversation_history.append({"role": "user", "content": event.response})
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        return DetermineNamespacesEvent()

    @step(
        name=LocaleString(en="Process Approval"),
        description=LocaleString(en="Processes user's approval and forwards to RAG or loops back"),
        icon="tabler:check",
    )
    async def process_approval_step(
        self,
        event: NamespaceApprovalResponseEvent,
        agent_config: NamespaceSelectionAgentConfig,
        run_context: RunContext,
        thread_context: ThreadContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> AgentInTheLoop.request | DetermineNamespacesEvent:
        """Store selection and forward to RAG if approved, or loop back if rejected."""
        if event.response:  # User approved
            await displayer.display_thought(t("agent.namespace_selection.thoughts.selection_approved"))

            selected: dict[str, str] = await run_context.get(PROPOSED_NAMESPACES_KEY, {})
            await thread_context.set(NAMESPACE_SELECTION_KEY, selected)

            # Reconstruct original event for forwarding
            original_messages = await run_context.get(ORIGINAL_MESSAGES_KEY, [])
            original_user = await run_context.get(ORIGINAL_USER_KEY)
            original_locale = await run_context.get(ORIGINAL_LOCALE_KEY)
            original_files = await run_context.get(ORIGINAL_FILES_KEY, [])

            messages = [ChatMessage.model_validate(m) for m in original_messages]
            user = UserIdentity.model_validate(original_user) if original_user else None
            files = [UserUploadedFile.model_validate(f) for f in original_files] if original_files else []

            namespace_pairs = [
                BucketNamespacePair(bucket_name=bucket, namespace_name=namespace)
                for bucket, namespace in selected.items()
            ]

            await displayer.display_thought(t("agent.namespace_selection.thoughts.forwarding_to_rag"))

            return AgentInTheLoop.invoke(
                agent_class=agent_config.rag_delegation.rag_agent_class,
                agent_id=agent_config.rag_delegation.rag_agent_id,
                start_event=NamespaceAwareStartEvent(
                    messages=messages,
                    user=user,
                    locale=original_locale,
                    files=files,
                    selected_namespaces=namespace_pairs,
                ),
                share_thread_id=True,
            )

        # User rejected - add the assistant's question and rejection to conversation, then loop back
        await displayer.display_thought(t("agent.namespace_selection.thoughts.selection_rejected"))

        conversation_history: list[dict[str, str]] = await run_context.get(CONVERSATION_HISTORY_KEY, [])
        conversation_history.append({"role": "assistant", "content": event.request_event.question})
        conversation_history.append(
            {
                "role": "user",
                "content": t("agent.namespace_selection.messages.user_rejected_selection"),
            }
        )
        await run_context.set(CONVERSATION_HISTORY_KEY, conversation_history)

        return DetermineNamespacesEvent()

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
