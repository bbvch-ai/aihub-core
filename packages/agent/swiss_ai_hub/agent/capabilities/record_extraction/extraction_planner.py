import asyncio
from itertools import accumulate

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import (
    KnowledgeContentSearchTimeoutError,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSelector,
    KnowledgeDocumentSummary,
    RecordSchema,
    RecordSchemaBuilder,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_continuation import ExtractionContinuation
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import CRITERIA_CHARACTERS
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

# One budget covers listing and searching the collections; a model's tool call already ran the search, and this second
# run decides what is extracted, so it may take longer rather than fail.
SELECTION_TIMEOUT_SECONDS = 20.0
# Documents a too broad selection shows rows from, so the user sees the columns and rows before committing.
SAMPLE_DOCUMENTS = 3
_SUMMARY = "agent.record_extraction.summary"


class ExtractionPlanner:
    """Turns an extraction request into one request per document, or into its answer when there is nothing to do.

    The selection is resolved here rather than taken from the model: the profile's glob and limits apply whatever the
    model asked for. A selection one answer can extract is extracted whole. A larger one is never cut: the answer shows
    a sample, how the documents break down by folder and year, and offers to narrow the request or to continue part by
    part; above the profile's ceiling only narrowing is offered. Problems the user can act on, such as a bad pattern, a
    slow search or a schema the model could not design, answer the request instead of failing the run.
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
        if request.continue_pending or request.selection is None:
            return await ExtractionContinuation.next(request, config, displayer, t, thread)
        settings = config.record_extraction
        try:
            selected = await KnowledgeDocumentSelector.resolve(
                request.collections,
                request.selection,
                settings.max_documents_total,
                config.knowledge_documents.path_glob or None,
                SELECTION_TIMEOUT_SECONDS,
            )
            if not selected.documents:
                return ExtractionPlanner.answer(request, t(f"{_SUMMARY}.no_documents"))
            await asyncio.to_thread(config.extraction_llm().get_model_info)
            async with config.llm.cost_reporting_llm(displayer, user=user) as llm:
                schema = await RecordSchemaBuilder.build(request.fields, llm, t)
        except (ValueError, LookupError, KnowledgeContentSearchTimeoutError) as problem:
            return ExtractionPlanner.answer(request, t(f"{_SUMMARY}.not_started", reason=problem))
        await PendingExtraction.clear(thread)
        parts = ExtractionEstimate.batches(
            selected.documents, settings.max_files, settings.minutes_per_turn, settings.max_parallel_extractions
        )
        if len(parts) == 1 and not selected.truncated:
            run = ExtractionPlanner._run(request, selected.documents, schema)
            minutes = ExtractionEstimate.minutes(selected.documents, settings.max_parallel_extractions)
            await displayer.display_thought(
                t(
                    "agent.record_extraction.progress.plan",
                    files=run.file_count,
                    fields=", ".join(run.field_names),
                    criteria=run.criteria,
                    minutes=minutes,
                )
            )
            return ExtractionPlanner.requests(run, selected.documents, schema, request.instructions, request.row_terms)
        return await ExtractionPlanner._too_broad(request, selected, parts, schema, config, displayer, t, thread)

    @staticmethod
    async def _too_broad(
        request: ExtractRecordsEvent,
        selected: KnowledgeDocumentSelectionResult,
        parts: list[list[KnowledgeDocumentSummary]],
        schema: RecordSchema,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
    ) -> list[DocumentExtractionRequestedEvent]:
        """A sample of the selection, with what the user can do about the rest; the rest waits in the conversation."""
        documents = selected.documents
        parallel = config.record_extraction.max_parallel_extractions
        if selected.truncated:
            notices = [t(f"{_SUMMARY}.too_broad_ceiling", total=len(documents))]
        else:
            minutes = ExtractionEstimate.minutes(documents, parallel)
            notices = [t(f"{_SUMMARY}.too_broad", total=len(documents), minutes=minutes)]
        notices.extend(SelectionFacets.lines(documents, t, counted=not selected.truncated))
        if selected.truncated:
            notices.append(t(f"{_SUMMARY}.options_narrow"))
        else:
            per_part = max(ExtractionEstimate.minutes(part, parallel) for part in parts)
            notices.append(t(f"{_SUMMARY}.options_parts", total=len(documents), parts=len(parts), minutes=per_part))
            await ExtractionPlanner._pending(request, documents, parts, schema).save(thread)
        sample = SelectionFacets.sample(documents, SAMPLE_DOCUMENTS)
        run = ExtractionPlanner._run(request, sample, schema).model_copy(
            update={
                "notices": [*notices, *request.notices],
                "sample": True,
                "total_documents": len(documents),
                "above_ceiling": selected.truncated,
                "parts": len(parts),
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
    def _pending(
        request: ExtractRecordsEvent,
        documents: list[KnowledgeDocumentSummary],
        parts: list[list[KnowledgeDocumentSummary]],
        schema: RecordSchema,
    ) -> PendingExtraction:
        return PendingExtraction(
            extraction_id=request.event_id,
            documents=documents,
            part_starts=[0, *accumulate(len(part) for part in parts[:-1])],
            record_schema=schema,
            instructions=request.instructions,
            row_terms=request.row_terms,
            criteria=ExtractionPlanner._criteria(request),
            collections=request.collections,
            show_collection=ExtractionPlanner._spans_collections(documents),
        )

    @staticmethod
    def requests(
        run: ExtractionRun,
        documents: list[KnowledgeDocumentSummary],
        schema: RecordSchema,
        instructions: str | None,
        row_terms: str | None,
    ) -> list[DocumentExtractionRequestedEvent]:
        return [
            DocumentExtractionRequestedEvent(
                run=run,
                document=document,
                record_schema=schema,
                instructions=instructions,
                row_terms=row_terms,
            )
            for document in documents
        ]

    @staticmethod
    def _run(
        request: ExtractRecordsEvent, documents: list[KnowledgeDocumentSummary], schema: RecordSchema
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
        )

    @staticmethod
    def _spans_collections(documents: list[KnowledgeDocumentSummary]) -> bool:
        return len({(doc.collection.bucket_name, doc.collection.namespace_name) for doc in documents}) > 1

    @staticmethod
    def _criteria(request: ExtractRecordsEvent) -> str:
        """How the documents were chosen, short enough to ride on every document's event and in the summary."""
        any_of = request.selection.any_of if request.selection else []
        described = " OR ".join(ExtractionPlanner._describe(criteria) for criteria in any_of)
        if len(described) <= CRITERIA_CHARACTERS:
            return described
        return described[: CRITERIA_CHARACTERS - 1] + "…"

    @staticmethod
    def _describe(criteria: KnowledgeDocumentCriteria) -> str:
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
