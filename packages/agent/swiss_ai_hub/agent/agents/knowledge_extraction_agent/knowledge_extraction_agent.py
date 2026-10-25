import asyncio
from typing import ClassVar

from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolLoopMode,
    ToolResultEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.continuation_tools import (
    CONTINUE_EXTRACTION_TOOL,
    ContinuationTools,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.discovery_prompt import DiscoveryPrompt
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ExtractionAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_notices import ExtractionNotices
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_call import SelectionCall
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback import SelectionFallback
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import KnowledgeDocumentTools
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import RecordSelectionTools
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class KnowledgeExtractionAgent(Agent):
    """Turns one chat message into one table across many knowledge documents, every row naming its file.

    The model finds the documents in a bounded loop over the document tools and settles them with
    `select_knowledge_documents`; the selection is then re-resolved within the profile's glob and file limit, and
    `RecordExtraction` extracts every document in parallel. The table is the answer, streamed as assembled.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.knowledge_extraction_agent.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.knowledge_extraction_agent.metadata.description"
    )
    icon: ClassVar[str] = "mdi:table-search"
    tools = ToolLoop.over(KnowledgeDocumentTools, RecordSelectionTools, ContinuationTools)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.contextualize.name"),
        description=AgentLocaleString.from_i18n_path(
            "agent.knowledge_extraction_agent.steps.contextualize.description"
        ),
        icon="mage:edit",
    )
    async def contextualize_step(
        self,
        event: UserMessageEvent,
        agent_config: KnowledgeExtractionAgentConfig,
        t: LocaleHandler,
        thread: ThreadContext,
        access: AccessChecker | None = None,
    ) -> Conversation.ContextualizeRequest:
        """The instructions, naming the run's collections and glob and any extraction an earlier answer left
        unfinished, lead the conversation the loop works on."""
        scope = await asyncio.to_thread(
            KnowledgeDocumentScope.of, agent_config, event.knowledge_references, access, t.locale
        )
        instructions = agent_config.instructions.in_locale(event.locale) if agent_config.instructions else None
        pending = await PendingExtraction.load(thread)
        history = DiscoveryPrompt.history(
            event.messages,
            scope,
            instructions,
            agent_config.number_of_input_tokens,
            t,
            pending,
            semantic=agent_config.knowledge_documents.semantic_search is True,
        )
        return Conversation.contextualize(history=history, message=event)

    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.discover.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.discover.description"),
        icon="mdi:file-search-outline",
    )
    async def discover_step(
        self,
        ctx: Conversation.Contextualized,
        event: UserMessageEvent,
        agent_config: KnowledgeExtractionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
        access: AccessChecker | None = None,
    ) -> ToolLoop.RunRequest | Conversation.CompleteRequest:
        """Let the model find the documents; with no collection the user may read, say so instead of looping over
        nothing, since the document tools cannot withhold themselves. Continuing is offered only while an earlier
        answer left an extraction unfinished."""
        scope = await asyncio.to_thread(
            KnowledgeDocumentScope.of, agent_config, event.knowledge_references, access, t.locale
        )
        if not scope.collections:
            notices = [
                t("agent.knowledge_extraction_agent.messages.no_collections"),
                *ExtractionNotices.for_table(scope, False, t),
            ]
            return await ExtractionAnswer.notice("\n\n".join(notices), ctx.query, displayer)
        pending = await PendingExtraction.load(thread)
        offered = None
        if pending is None or not (pending.overflow_rows or pending.remaining_documents):
            offered = [name for name in KnowledgeExtractionAgent.tools.names() if name != CONTINUE_EXTRACTION_TOOL]
        loop = KnowledgeExtractionAgent.tools.run(
            ctx.history, mode=ToolLoopMode.GATHER, tools=offered, knowledge_references=event.knowledge_references
        )
        return loop.model_copy(update={"hands_back_results": False})

    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.plan.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.plan.description"),
        icon="mdi:table-search",
        max_executions_per_run=1,
    )
    async def plan_step(
        self,
        finished: ToolLoop.Finished,
        ctx: Conversation.Contextualized,
        event: UserMessageEvent,
        agent_config: KnowledgeExtractionAgentConfig,
        displayer: EventDisplayer,
        t: LocaleHandler,
        decided: list[ToolCallsDecidedEvent] | None = None,
        calls: list[ToolCallApprovedEvent] | None = None,
        results: list[ToolResultEvent] | None = None,
        access: AccessChecker | None = None,
        user: UserIdentity | None = None,
    ) -> RecordExtraction.ExtractRequest | Conversation.CompleteRequest:
        """Extract from the documents the model settled on, re-resolved within the profile's limits. A model that
        ended its search without stating a selection is asked once for the selection its searches point to; one stopped
        at its limit before it did is asked for folders and paths only, since its hits are incomplete. A stopped search
        whose own selection stands still marks the table as possibly incomplete."""
        scope = await asyncio.to_thread(
            KnowledgeDocumentScope.of, agent_config, event.knowledge_references, access, t.locale
        )
        if SelectionCall.continued(decided, calls, results):
            notices = ExtractionNotices.for_table(scope, finished.stopped_early, t)
            return RecordExtraction.continue_pending(scope.pairs(), notices)
        selection = SelectionCall.last(decided, calls, results)
        by_location = selection is None and finished.stopped_early
        if selection is None:
            selection = await SelectionFallback.ask(
                ctx.query, calls or [], results or [], scope, agent_config.llm, displayer, user, t, by_location
            )
        if selection is None:
            notices = [
                ExtractionNotices.without_selection(agent_config, finished.stopped_early, t),
                *ExtractionNotices.for_table(scope, False, t),
            ]
            return await ExtractionAnswer.notice("\n\n".join(notices), ctx.query, displayer)
        return RecordExtraction.extract(
            selection.selection,
            selection.fields,
            scope.pairs(),
            selection.instructions,
            selection.row_terms,
            notices=ExtractionNotices.for_table(scope, finished.stopped_early, t, by_location),
            cut_short=finished.stopped_early and not by_location,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.complete.name"),
        description=AgentLocaleString.from_i18n_path("agent.knowledge_extraction_agent.steps.complete.description"),
        icon="mage:message",
    )
    async def complete_step(
        self, extracted: RecordExtraction.Extracted, ctx: Conversation.Contextualized, displayer: EventDisplayer
    ) -> Conversation.CompleteRequest:
        """The table is the answer: stream it with its summary and complete the run."""
        return await ExtractionAnswer.table(extracted, ctx.query, displayer)
