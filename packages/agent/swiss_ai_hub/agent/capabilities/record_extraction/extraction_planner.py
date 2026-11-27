import asyncio

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import (
    DocumentMetadataCounts,
    DocumentMetadataFilter,
    KnowledgeContentSearchTimeoutError,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSelector,
    KnowledgeDocumentSummary,
    PathDateCounts,
    PathDateVerdict,
    RecordSchema,
    RecordSchemaBuilder,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_condition_text import DocumentConditionText
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_sample import SAMPLE_ABOVE_DOCUMENTS, ExtractionSample
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import CRITERIA_CHARACTERS, ExtractionTable
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.sample_awaiting_confirmation import SampleAwaitingConfirmation
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

# One budget covers listing and searching the collections; a model's tool call already ran the search, and this second
# run decides what is extracted, so it may take longer rather than fail.
SELECTION_TIMEOUT_SECONDS = 20.0
_SUMMARY = "agent.record_extraction.summary"


class ExtractionPlanner:
    """Turns an extraction request into one request per document, or into its answer when there is nothing to do.

    The selection is resolved here rather than taken from the model: the profile's glob and ceiling apply whatever the
    model asked for. One answer extracts the whole selection, however long that takes; nothing is cut and nothing is
    left for later. A selection larger than `SAMPLE_ABOVE_DOCUMENTS` is first sampled, documents likely to hold wanted
    rows first, and extracted whole once the user confirms; above the profile's ceiling only narrowing is offered.
    Problems the user can act on, such as a bad pattern, a slow search or a schema the model could not design, answer
    the request instead of failing the run.
    """

    @staticmethod
    async def plan(
        request: ExtractRecordsEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
        user: UserIdentity | None,
    ) -> list[DocumentExtractionRequestedEvent] | RecordsExtractedEvent:
        prepared = await ExtractionPlanner._with_waiting_sample(request, config.agent_id, thread, t)
        if isinstance(prepared, RecordsExtractedEvent):
            return prepared
        request, schema = prepared
        try:
            selected = await KnowledgeDocumentSelector.resolve(
                request.collections,
                request.selection,
                config.record_extraction.max_documents_total,
                config.knowledge_documents.path_glob or None,
                SELECTION_TIMEOUT_SECONDS,
            )
            if not selected.documents:
                return ExtractionPlanner.answer(request, ExtractionPlanner._nothing_selected(selected, t))
            schema = schema or await ExtractionPlanner._schema(request, config, displayer, user, t)
        except (ValueError, LookupError, KnowledgeContentSearchTimeoutError) as problem:
            return ExtractionPlanner.answer(request, t(f"{_SUMMARY}.not_started", reason=problem))
        if selected.truncated or (len(selected.documents) > SAMPLE_ABOVE_DOCUMENTS and not request.confirmed):
            return await ExtractionPlanner._sample(request, selected, schema, config, displayer, t, thread, user)
        return await ExtractionPlanner._whole(request, selected, schema, config, displayer, t, user)

    @staticmethod
    def _nothing_selected(selected: KnowledgeDocumentSelectionResult, t: LocaleHandler) -> str:
        """That nothing was selected, and, when the period left out every document, how many, which and which years,
        so the user sees a request for the wrong period rather than an empty scope."""
        lines = [t(f"{_SUMMARY}.no_documents")]
        counts = selected.path_dates
        if counts is not None and counts.total > 0:
            lines.extend(ExtractionTable.path_date_lines(counts, t))
            if counts.outside_years:
                years = ", ".join(str(year) for year in counts.outside_years)
                lines.append(t(f"{_SUMMARY}.path_dates_years", years=years))
        if selected.metadata is not None and selected.metadata.total > 0:
            lines.extend(ExtractionTable.metadata_lines(selected.metadata, t))
        return "\n\n".join(lines)

    @staticmethod
    async def _with_waiting_sample(
        request: ExtractRecordsEvent, agent_id: str, thread: ThreadContext, t: LocaleHandler
    ) -> tuple[ExtractRecordsEvent, RecordSchema | None] | RecordsExtractedEvent:
        """A confirmation takes the waiting sample's selection and columns, or answers that there is none; a new
        request voids the waiting sample, so a later "yes" never extracts a selection the user moved on from."""
        if not (request.confirmed or request.selection is None):
            await SampleAwaitingConfirmation.clear(thread, agent_id)
            return request, None
        awaiting = await SampleAwaitingConfirmation.take(thread, agent_id)
        if awaiting is None or not awaiting.within(request.collections):
            reason = "nothing_awaiting" if awaiting is None else "scope_changed"
            return ExtractionPlanner.answer(request, t(f"{_SUMMARY}.{reason}"))
        return awaiting.as_request(request), awaiting.record_schema

    @staticmethod
    async def _schema(
        request: ExtractRecordsEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        user: UserIdentity | None,
        t: LocaleHandler,
    ) -> RecordSchema:
        await asyncio.to_thread(config.extraction_llm().get_model_info)
        async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
            return await RecordSchemaBuilder.build(request.fields, llm, t)

    @staticmethod
    async def _whole(
        request: ExtractRecordsEvent,
        selected: KnowledgeDocumentSelectionResult,
        schema: RecordSchema,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> list[DocumentExtractionRequestedEvent]:
        """Every document in one answer, the likeliest first when the selection is large, so early progress shows what
        the table will hold; a small selection is not worth a ranking's wait."""
        documents = selected.documents
        query = ExtractionPlanner._semantic_query(request, config, t)
        if len(documents) > SAMPLE_ABOVE_DOCUMENTS:
            documents, _ = await ExtractionSample.ordered(
                documents,
                request.collections,
                request.document_terms,
                request.row_terms,
                semantic_query=query,
                user=user,
                path_glob=config.knowledge_documents.path_glob or None,
            )
        run = ExtractionPlanner._run(request, documents, schema, selected.path_dates, selected.metadata)
        minutes = ExtractionEstimate.minutes(documents, config.record_extraction.max_parallel_extractions)
        await displayer.display_thought(
            t(
                "agent.record_extraction.progress.plan",
                files=run.file_count,
                fields=", ".join(run.field_names),
                criteria=run.criteria,
                minutes=minutes,
            )
        )
        return ExtractionPlanner.requests(run, documents, schema, request.instructions, request.row_terms)

    @staticmethod
    async def _sample(
        request: ExtractRecordsEvent,
        selected: KnowledgeDocumentSelectionResult,
        schema: RecordSchema,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
        user: UserIdentity | None,
    ) -> list[DocumentExtractionRequestedEvent]:
        """A sample from documents likely to hold wanted rows, what the table will hold and cost, and what the user
        can do: confirm, or narrow; above the ceiling only narrow."""
        documents = selected.documents
        ordered, likely = await ExtractionSample.ordered(
            documents,
            request.collections,
            request.document_terms,
            request.row_terms,
            semantic_query=ExtractionPlanner._semantic_query(request, config, t),
            user=user,
            path_glob=config.knowledge_documents.path_glob or None,
        )
        sample = ExtractionSample.pick(ordered, likely=likely)
        notices = ExtractionPlanner._sample_notices(request, selected, schema, config, t)
        if not selected.truncated:
            await SampleAwaitingConfirmation.of(request, schema, len(documents)).save(thread, config.agent_id)
        run = ExtractionPlanner._run(request, sample, schema, selected.path_dates, selected.metadata).model_copy(
            update={
                "notices": [*notices, *request.notices],
                "sample": True,
                "total_documents": len(documents),
                "above_ceiling": selected.truncated,
                "show_collection": ExtractionPlanner._spans_collections(documents),
            }
        )
        await displayer.display_thought(
            t(
                "agent.record_extraction.progress.sample",
                total=len(documents),
                files=len(sample),
                fields=", ".join(run.field_names),
            )
        )
        return ExtractionPlanner.requests(run, sample, schema, request.instructions, request.row_terms)

    @staticmethod
    def _semantic_query(request: ExtractRecordsEvent, config: RecordExtractionFields, t: LocaleHandler) -> str | None:
        """What the wanted documents are about, to rank them by meaning: the terms that identify them and the
        conditions on them, their period included, and on their rows, in the user's words. Not after a discovery
        search, whose model already ranked what it chose."""
        if config.knowledge_documents.discovery is True:
            return None
        parts = (request.document_terms, ExtractionPlanner._condition(request, t), request.instructions, request.fields)
        return " ".join(part for part in parts if part) or None

    @staticmethod
    def _condition(request: ExtractRecordsEvent, t: LocaleHandler) -> str | None:
        """The document condition with the selection's period in words, as the user reads it."""
        date_range = request.selection.path_date_range if request.selection else None
        return DocumentConditionText.of(request.document_condition, date_range, t)

    @staticmethod
    def _sample_notices(
        request: ExtractRecordsEvent,
        selected: KnowledgeDocumentSelectionResult,
        schema: RecordSchema,
        config: RecordExtractionFields,
        t: LocaleHandler,
    ) -> list[str]:
        """How many documents match, what the table would hold, how they break down, and the choice."""
        documents = selected.documents
        columns = ", ".join(name.replace("_", " ") for name in schema.field_names)
        kept = request.instructions or t(f"{_SUMMARY}.every_row")
        condition = ExtractionPlanner._condition(request, t)
        notices = [
            t(f"{_SUMMARY}.too_broad_ceiling", total=len(documents))
            if selected.truncated
            else t(
                f"{_SUMMARY}.too_broad",
                total=len(documents),
                minutes=ExtractionEstimate.minutes(documents, config.record_extraction.max_parallel_extractions),
            ),
            t(f"{_SUMMARY}.interpretation_documents", columns=columns, documents=condition, kept=kept)
            if condition
            else t(f"{_SUMMARY}.interpretation", columns=columns, kept=kept),
            *SelectionFacets.lines(documents, t, counted=not selected.truncated),
            *(ExtractionTable.metadata_lines(selected.metadata, t) if selected.metadata is not None else []),
        ]
        notices.append(
            t(f"{_SUMMARY}.options_narrow")
            if selected.truncated
            else t(f"{_SUMMARY}.options_confirm", total=len(documents))
        )
        return notices

    @staticmethod
    def requests(
        run: ExtractionRun,
        documents: list[KnowledgeDocumentSummary],
        schema: RecordSchema,
        instructions: str | None,
        row_terms: str | None,
    ) -> list[DocumentExtractionRequestedEvent]:
        """One request per document; a document its path dates wholly within the run's period is not judged on it."""
        return [
            DocumentExtractionRequestedEvent(
                run=run,
                document=document,
                record_schema=schema,
                instructions=instructions,
                row_terms=row_terms,
                dated_by_path=run.period is not None and run.period.verdict(document.path) is PathDateVerdict.WITHIN,
            )
            for document in documents
        ]

    @staticmethod
    def _run(
        request: ExtractRecordsEvent,
        documents: list[KnowledgeDocumentSummary],
        schema: RecordSchema,
        path_dates: PathDateCounts | None = None,
        metadata: DocumentMetadataCounts | None = None,
    ) -> ExtractionRun:
        return ExtractionRun(
            extraction_id=request.event_id,
            file_count=len(documents),
            field_names=schema.field_names,
            criteria=ExtractionPlanner._criteria(request),
            notices=list(request.notices),
            cut_short=request.cut_short,
            show_collection=ExtractionPlanner._spans_collections(documents),
            tool_call_id=request.tool_call_id,
            collections=request.collections,
            document_condition=request.document_condition,
            period=request.selection.path_date_range if request.selection else None,
            path_dates=path_dates,
            metadata=metadata,
        )

    @staticmethod
    def _spans_collections(documents: list[KnowledgeDocumentSummary]) -> bool:
        return len({(doc.collection.bucket_name, doc.collection.namespace_name) for doc in documents}) > 1

    @staticmethod
    def _criteria(request: ExtractRecordsEvent) -> str:
        """How the documents were chosen, short enough to ride on every document's event and in the summary."""
        any_of = request.selection.any_of if request.selection else []
        described = ExtractionPlanner.describe_any_of(any_of)
        metadata_filter = request.selection.metadata_filter if request.selection else None
        if metadata_filter is not None:
            described = f"{described}; {ExtractionPlanner.describe_metadata(metadata_filter)}"
        if len(described) <= CRITERIA_CHARACTERS:
            return described
        return described[: CRITERIA_CHARACTERS - 1] + "…"

    @staticmethod
    def describe_any_of(any_of: list[KnowledgeDocumentCriteria]) -> str:
        """How a selection's criteria read in a summary or a form, e.g. "text contains `Acme` OR path matches ..."."""
        return " OR ".join(ExtractionPlanner.describe(criteria) for criteria in any_of)

    @staticmethod
    def describe(criteria: KnowledgeDocumentCriteria) -> str:
        code = ExtractionPlanner._code
        searched = "matches" if criteria.content_is_regex else "contains"
        parts = [
            f"path matches {code(criteria.path_glob)}" if criteria.path_glob else "",
            f"path contains {code(criteria.path_regex)}" if criteria.path_regex else "",
            f"text {searched} {code(criteria.content_query)}" if criteria.content_query else "",
            f"{len(criteria.document_ids)} chosen documents" if criteria.document_ids else "",
        ]
        return " and ".join(part for part in parts if part) or "every document"

    @staticmethod
    def describe_metadata(metadata_filter: DocumentMetadataFilter) -> str:
        """The filter as it reads in a summary, e.g. "type `contract` and `document_parties` contains `Hooli`"."""
        code = ExtractionPlanner._code
        parts = [f"type {' or '.join(code(name) for name in metadata_filter.types)}"] if metadata_filter.types else []
        for condition in metadata_filter.conditions:
            if condition.contains is not None:
                parts.append(f"{code(condition.attribute)} contains {code(condition.contains)}")
                continue
            bounds = [
                f">= {condition.at_least}" if condition.at_least else "",
                f"<= {condition.at_most}" if condition.at_most else "",
            ]
            currency = f" {condition.currency}" if condition.currency else ""
            parts.append(f"{code(condition.attribute)} {' and '.join(bound for bound in bounds if bound)}{currency}")
        return " and ".join(parts)

    @staticmethod
    def _code(value: str) -> str:
        """A code span, so a glob's `**` is not read as bold where the summary is rendered as markdown."""
        return f"`` {value} ``" if "`" in value else f"`{value}`"

    @staticmethod
    def answer(request: ExtractRecordsEvent, summary: str) -> RecordsExtractedEvent:
        return RecordsExtractedEvent(
            extraction_id=request.event_id,
            summary="\n\n".join([summary, *request.notices]),
            truncated=request.cut_short,
            tool_call_id=request.tool_call_id,
        )
