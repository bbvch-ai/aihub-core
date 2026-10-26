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
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.discovery_prompt import DiscoveryPrompt
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_answer import ExtractionAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_notices import ExtractionNotices
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.knowledge_extraction_agent_config import (
    KnowledgeExtractionAgentConfig,
)
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_call import SelectionCall
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback import SelectionFallback
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.whole_scope_request import WholeScopeRequest
from swiss_ai_hub.agent.capabilities.conversation.conversation import Conversation
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import KnowledgeDocumentTools
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_selection_tools import RecordSelectionTools
from swiss_ai_hub.agent.capabilities.record_extraction.sample_awaiting_confirmation import SampleAwaitingConfirmation
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop import ToolLoop
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class KnowledgeExtractionAgent(Agent):
    """Turns one chat message into one table across many knowledge documents, every row naming its file.

    By default every document in the profile's collections and glob is read, narrowed only by the folders, files or
    years the user names, so the table cannot miss a document for its wording; one structured call reads the columns
    and the row condition from the message. With `discovery`, the model instead finds the documents in a bounded loop
    over the document tools and settles them with `select_knowledge_documents`. Either way the selection is resolved
    within the profile's glob and ceiling, `RecordExtraction` extracts every document in parallel (a large selection
    after the user confirmed its sample), and the table's preview is the answer, its whole as a file.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.knowledge_extraction_agent.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.knowledge_extraction_agent.metadata.description"
    )
    icon: ClassVar[str] = "mdi:table-search"
    tools = ToolLoop.over(KnowledgeDocumentTools, RecordSelectionTools)

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
        access: AccessChecker | None = None,
    ) -> Conversation.ContextualizeRequest:
        """The instructions, naming the run's collections and glob, lead the conversation the loop works on."""
        scope = await asyncio.to_thread(
            KnowledgeDocumentScope.of, agent_config, event.knowledge_references, access, t.locale
        )
        instructions = agent_config.instructions.in_locale(event.locale) if agent_config.instructions else None
        history = DiscoveryPrompt.history(
            event.messages,
            scope,
            instructions,
            agent_config.input_budget,
            t,
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
        user: UserIdentity | None = None,
    ) -> ToolLoop.RunRequest | RecordExtraction.ExtractRequest | Conversation.CompleteRequest:
        """Read the request and extract from the whole scope, or, with discovery, let the model find the documents.
        With no collection the user may read, say so instead of looping over nothing. While a sample awaits the
        user's decision, the message is read first in either mode, since only that tells a "yes" from a new request."""
        scope = await asyncio.to_thread(
            KnowledgeDocumentScope.of, agent_config, event.knowledge_references, access, t.locale
        )
        if not scope.collections:
            notices = [
                t("agent.knowledge_extraction_agent.messages.no_collections"),
                *ExtractionNotices.for_table(scope, False, t),
            ]
            return await ExtractionAnswer.notice("\n\n".join(notices), ctx.query, displayer)
        awaiting = await SampleAwaitingConfirmation.load(thread, agent_config.agent_id)
        if not agent_config.discovery or awaiting is not None:
            extraction = await WholeScopeRequest.extraction(
                ctx.history, scope, agent_config, awaiting, displayer, user, t, event.locale
            )
            if isinstance(extraction, str):
                return await ExtractionAnswer.notice(extraction, ctx.query, displayer)
            if extraction is not None:
                return extraction
        loop = KnowledgeExtractionAgent.tools.run(
            ctx.history, mode=ToolLoopMode.GATHER, knowledge_references=event.knowledge_references
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
            document_terms=selection.document_terms,
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
