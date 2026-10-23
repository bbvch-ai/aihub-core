from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentListing, KnowledgeDocumentSummary
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_progress import ExtractionProgress
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

_SUMMARY = "agent.record_extraction.summary"


class ExtractionContinuation:
    """The next part of the extraction this conversation left pending: rows still to show first, then the next
    documents, with the columns the extraction started with.

    Documents are loaded within the scope of the run that continues: a document outside the profile's current path
    filter is left out and the answer says so, and a collection the user may no longer read, or a profile that dropped
    it, ends the extraction, carried-over rows included. The part is marked taken before it runs, so a repeated
    continue goes on with the next one; one whose run died before its table was assembled is extracted again once every
    other part was taken, so the totals never count documents that were not extracted.
    """

    @staticmethod
    async def next(
        request: ExtractRecordsEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        thread: ThreadContext,
    ) -> list[DocumentExtractionRequestedEvent] | RecordsExtractedEvent:
        pending = await PendingExtraction.load(thread)
        allowed = {(pair.bucket_name, pair.namespace_name) for pair in request.collections}
        if pending is not None and any(
            (pair.bucket_name, pair.namespace_name) not in allowed for pair in pending.collections
        ):
            await PendingExtraction.clear(thread)
            notices = [*request.notices, t(f"{_SUMMARY}.scope_changed")]
            return ExtractionContinuation._answer(request, "\n\n".join(notices))
        if pending is not None and pending.overflow_rows:
            return await ExtractionProgress.more_rows(request, pending, config, thread, t)
        index = pending.following_part if pending is not None else None
        if pending is None or index is None or pending.record_schema is None:
            await PendingExtraction.clear(thread)
            notices = [t(f"{_SUMMARY}.nothing_pending"), *request.notices]
            return ExtractionContinuation._answer(request, "\n\n".join(notices))
        planned = pending.part(index)
        documents = [doc for doc in planned if (doc.collection.bucket_name, doc.collection.namespace_name) in allowed]
        if config.knowledge_documents.path_glob:
            listing = KnowledgeDocumentListing.from_summaries(documents)
            matching = {
                ExtractionContinuation._key(doc)
                for doc in listing.matching_glob(config.knowledge_documents.path_glob).documents
            }
            documents = [doc for doc in documents if ExtractionContinuation._key(doc) in matching]
        notices = list(request.notices)
        if len(documents) < len(planned):
            notices.append(t(f"{_SUMMARY}.gone", count=len(planned) - len(documents)))
        pending = pending.taking(index)
        await pending.save(thread)
        if not documents:
            answer = ExtractionContinuation._answer(request, "\n\n".join(notices))
            return await ExtractionProgress.skipped(answer, pending.finishing(index), config, thread, t)
        run = ExtractionRun(
            extraction_id=request.event_id,
            file_count=len(documents),
            field_names=pending.record_schema.field_names,
            criteria=pending.criteria,
            notices=notices,
            show_collection=pending.show_collection,
            tool_call_id=request.tool_call_id,
            collections=pending.collections,
            part=index + 1,
            parts=pending.part_count,
            first_document=pending.part_starts[index] + 1,
            total_documents=len(pending.documents),
        )
        minutes = ExtractionEstimate.minutes(documents, config.record_extraction.max_parallel_extractions)
        await displayer.display_thought(
            t(
                "agent.record_extraction.progress.part",
                part=run.part,
                parts=run.parts,
                files=len(documents),
                minutes=minutes,
                fields=", ".join(run.field_names),
            )
        )
        return [
            DocumentExtractionRequestedEvent(
                run=run,
                document=document,
                record_schema=pending.record_schema,
                instructions=pending.instructions,
                row_terms=pending.row_terms,
            )
            for document in documents
        ]

    @staticmethod
    def _key(document: KnowledgeDocumentSummary) -> tuple[str, str, str]:
        return document.collection.bucket_name, document.collection.namespace_name, document.id

    @staticmethod
    def _answer(request: ExtractRecordsEvent, summary: str) -> RecordsExtractedEvent:
        return RecordsExtractedEvent(extraction_id=request.event_id, summary=summary, tool_call_id=request.tool_call_id)
