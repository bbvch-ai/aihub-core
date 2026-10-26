import asyncio
from typing import ClassVar

from pydantic import ValidationError
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import AccessChecker, UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    ExtractRecordsEvent,
    RecordsExtractedEvent,
    RunToolLoopEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
)
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, KnowledgeDocumentSelection
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction import DocumentRecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_tool_arguments import (
    ExtractRecordsToolArguments,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner import ExtractionPlanner
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.records_tool_result import RecordsToolResult
from swiss_ai_hub.agent.capabilities.tool_loop.tool_approval_policy import ToolApprovalPolicy
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

EXTRACT_RECORDS_TOOL = "extract_records"
# The user, not the model, confirms a sample: an answer that showed one cannot also extract the whole selection.
# The key holds the call that used up this answer: a sample, or the confirmed extraction itself.
_ANSWER_USED_KEY = "record_extraction:answer_used"
_ONE_EXTRACTION_PER_ANSWER = (
    "This answer has already shown a sample or extracted a confirmed selection; the rest waits for the user. Do not "
    "call extract_records with confirm_sample now: tell the user what the sample shows and ask whether to go on."
)


@precondition()
async def every_document_answered(
    extracted: DocumentExtractedEvent,
    results: list[DocumentExtractedEvent],
    done: list[RecordsExtractedEvent] | None = None,
) -> bool:
    """The extraction the arriving result belongs to has a result for every document and no table yet.

    Results are counted per extraction and by distinct request, never by equality: a run may extract twice, and an
    event delivered twice must not count twice.
    """
    run = extracted.run
    answered = {result.request_event_id for result in results if result.run.extraction_id == run.extraction_id}
    assembled = any(table.extraction_id == run.extraction_id for table in done or [])
    return len(answered) >= run.file_count and not assembled


@precondition()
async def extracts_records(call: ToolCallApprovedEvent) -> bool:
    return call.name == EXTRACT_RECORDS_TOOL


@precondition()
async def answers_an_extraction_call(extracted: RecordsExtractedEvent, decided: ToolCallsDecidedEvent) -> bool:
    return extracted.tool_call_id is not None and extracted.tool_call_id in decided.tool_call_ids


class RecordExtraction(Capability):
    """
    One table across many knowledge documents, every row naming the file it came from:

    - `extract(selection, fields, collections, instructions, row_terms)` is answered with `RecordsExtractedEvent`:
      the selection is resolved within the profile's glob and ceiling, the columns are designed from `fields`, and
      every document is extracted in parallel before one table is assembled and stored as a file. A document that
      fails is listed, never fatal. A selection too large to extract unasked is sampled first, and `confirm_sample`
      extracts it whole once the user agrees.
    - In a tool set the model chooses when to extract (`extract_records`); the table then reaches the user from the
      result event itself, and the model reads its summary.
    """

    calls: ClassVar[dict] = {ExtractRecordsEvent: (RecordsExtractedEvent,)}
    required_config: ClassVar[type[RecordExtractionFields]] = RecordExtractionFields

    ExtractRequest = ExtractRecordsEvent
    Extracted = RecordsExtractedEvent

    tool_name: ClassVar[str] = EXTRACT_RECORDS_TOOL
    tool_config: ClassVar[type[RecordExtractionFields]] = RecordExtractionFields
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.record_extraction.tools.extract.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.record_extraction.tools.extract.approval"),
        default_approval=ToolApprovalPolicy.EVERY_CALL,
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered when the profile lets the model work on documents and the user may read some to extract from."""
        config = context.agent_config
        if not isinstance(config, RecordExtractionFields) or not config.knowledge_documents.enabled:
            return None
        scope = KnowledgeDocumentScope.of(config, context.knowledge_references, context.access, context.t.locale)
        if not scope.collections:
            return None
        return ToolDefinition(
            name=EXTRACT_RECORDS_TOOL,
            description=context.t("agent.record_extraction.tools.extract.description"),
            parameters=ExtractRecordsToolArguments.model_json_schema(),
        )

    @staticmethod
    def confirm_sample(collections: list[BucketNamespacePair], notices: list[str] | None = None) -> ExtractRecordsEvent:
        """Every document of the selection this conversation showed a sample of, within the run's own collections."""
        return ExtractRecordsEvent(fields="", collections=collections, notices=list(notices or []), confirmed=True)

    @staticmethod
    def extract(
        selection: KnowledgeDocumentSelection,
        fields: str,
        collections: list[BucketNamespacePair],
        instructions: str | None = None,
        row_terms: str | None = None,
        notices: list[str] | None = None,
        cut_short: bool = False,
        document_terms: str | None = None,
    ) -> ExtractRecordsEvent:
        return ExtractRecordsEvent(
            selection=selection,
            fields=fields,
            instructions=instructions,
            row_terms=row_terms,
            document_terms=document_terms,
            collections=collections,
            notices=list(notices or []),
            cut_short=cut_short,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.plan.name"),
        description=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.plan.description"),
        icon="mdi:table-search",
    )
    async def plan_extraction_step(
        agent: Agent,
        request: ExtractRecordsEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
        user: UserIdentity | None = None,
    ) -> list[DocumentExtractionRequestedEvent] | RecordsExtractedEvent:
        """Resolve the documents and design the columns, then ask for every document at once so they run in parallel;
        a selection too large to extract unasked gets a sample and waits in the conversation for the user's go-ahead."""
        return await ExtractionPlanner.plan(request, config, displayer, t, thread, user)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.extract.name"),
        description=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.extract.description"),
        icon="mdi:file-table-outline",
    )
    async def extract_document_step(
        agent: Agent,
        request: DocumentExtractionRequestedEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        redis: Redis,
        user: UserIdentity | None = None,
    ) -> DocumentExtractedEvent:
        """Extract one document's rows; it takes only its request, so it runs once per document."""
        return await DocumentRecordExtraction.extract(request, config, displayer, t, redis, user)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.assemble.name"),
        description=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.assemble.description"),
        icon="mdi:table-merge-cells",
        precondition=every_document_answered,
    )
    async def assemble_table_step(
        agent: Agent,
        extracted: DocumentExtractedEvent,
        results: list[DocumentExtractedEvent],
        t: LocaleHandler,
    ) -> RecordsExtractedEvent:
        """Join every document of the extraction the arriving result completes into one table, stored whole as a file
        and previewed on the event."""
        run = extracted.run
        own = [result for result in results if result.run.extraction_id == run.extraction_id]
        return await ExtractionTable.assemble(run, own, t)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.extract_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.extract_as_tool.description"),
        icon="mdi:table-search",
        precondition=extracts_records,
    )
    async def extract_tool_call_step(
        agent: Agent,
        call: ToolCallApprovedEvent,
        request: RunToolLoopEvent,
        tool: RecordExtractionFields,
        t: LocaleHandler,
        run_context: RunContext,
        access: AccessChecker | None = None,
    ) -> ExtractRecordsEvent | ToolResultEvent:
        """The model chose to extract: the same extraction as an explicit call, over the collections of this run."""
        scope = await asyncio.to_thread(KnowledgeDocumentScope.of, tool, request.knowledge_references, access, t.locale)
        try:
            arguments = ExtractRecordsToolArguments.model_validate(call.arguments)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        if arguments.confirm_sample:
            claimed = await run_context.set_if_absent(_ANSWER_USED_KEY, call.tool_call_id)
            if not claimed and await run_context.get(_ANSWER_USED_KEY) != call.tool_call_id:
                return ToolResultEvent(
                    tool_call_id=call.tool_call_id, name=call.name, content=_ONE_EXTRACTION_PER_ANSWER
                )
            event = RecordExtraction.confirm_sample(scope.pairs())
            return event.model_copy(update={"tool_call_id": call.tool_call_id})
        event = RecordExtraction.extract(
            arguments.selection,
            arguments.fields,
            scope.pairs(),
            arguments.instructions,
            arguments.row_terms,
            document_terms=arguments.document_terms,
        )
        return event.model_copy(update={"tool_call_id": call.tool_call_id})

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.record_extraction.steps.answer_tool_call.description"),
        icon="mdi:table-arrow-left",
        precondition=answers_an_extraction_call,
    )
    async def extract_tool_result_step(
        agent: Agent, extracted: RecordsExtractedEvent, decided: ToolCallsDecidedEvent, run_context: RunContext
    ) -> ToolResultEvent:
        """Hand the extraction back to the loop: the summary and the first rows for the model, which must not retype
        the table the user is already shown. A sample uses up the answer, so the model cannot extract the whole
        selection before the user agrees."""
        if extracted.awaiting_confirmation:
            await run_context.set(_ANSWER_USED_KEY, extracted.tool_call_id)
        return ToolResultEvent(
            tool_call_id=extracted.tool_call_id or "",
            name=EXTRACT_RECORDS_TOOL,
            content=RecordsToolResult.content(extracted),
        )
