import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import (
    ExtractionFileStore,
    KnowledgeDocumentReader,
    RecordExtractor,
    RecordSchema,
    RecordValue,
)
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_slots import ExtractionSlots
from swiss_ai_hub.agent.capabilities.record_extraction.reading_heartbeat import ReadingHeartbeat
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields

logger = logging.getLogger(__name__)

FAILURE_REASON_CHARACTERS = 300
# A document this long takes several extraction calls, so its start is announced: the chat otherwise shows nothing
# from it for minutes. About three windows of a mid-sized model.
LONG_DOCUMENT_CHARACTERS = 40_000
# The first rows a document yielded, shown with its progress so the user sees early what the table holds.
PREVIEW_ROWS_IN_PROGRESS = 2
PROGRESS_ROW_CHARACTERS = 120
# Parts of a document longer than the profile's full-read limit that are read: its opening and the parts most likely
# to hold wanted lines (see `WindowSelection`).
PARTIAL_READ_WINDOWS = 12
# The running count of an extraction's finished documents, for the progress the chat shows; kept briefly in Valkey
# because the documents finish in separate steps, possibly on separate replicas, and one answer may run for hours.
_DONE_KEY = "record_extraction:{extraction_id}:done"
_DONE_TTL_SECONDS = 86_400


class DocumentRecordExtraction:
    """Extracts the rows of one document of an extraction, always answering with a result.

    The join waits for one result per document, so a document that cannot be read or extracted answers with its
    failure instead of raising: a raise would either end the whole run or leave the join waiting.
    """

    @staticmethod
    async def extract(
        request: DocumentExtractionRequestedEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        redis: Redis,
        user: UserIdentity | None,
    ) -> DocumentExtractedEvent:
        settings = config.record_extraction
        rows: list[dict[str, RecordValue]] = []
        async with ExtractionSlots.documents(config.agent_id, settings.max_parallel_extractions):
            try:
                result, rows = await DocumentRecordExtraction._extract(request, config, displayer, t, user)
            except Exception as error:
                logger.exception("[record-extraction] %s failed", request.document.path)
                result = DocumentRecordExtraction._failed(request, f"{type(error).__name__}: {error}")
        try:
            await DocumentRecordExtraction._report(
                result, rows, await DocumentRecordExtraction._done(result, redis), displayer, t
            )
        except Exception:
            # Progress only: the result must still reach the join, or the table waits for this document forever.
            logger.warning("[record-extraction] could not report %s", request.document.path, exc_info=True)
        return result

    @staticmethod
    async def _done(result: DocumentExtractedEvent, redis: Redis) -> int:
        key = _DONE_KEY.format(extraction_id=result.run.extraction_id)
        done = await redis.incr(key)
        await redis.expire(key, _DONE_TTL_SECONDS)
        return done

    @staticmethod
    async def _extract(
        request: DocumentExtractionRequestedEvent,
        config: RecordExtractionFields,
        displayer: EventDisplayer,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> tuple[DocumentExtractedEvent, list[dict[str, RecordValue]]]:
        """The document's result, its rows stored rather than carried, and the rows themselves for the progress."""
        document = await KnowledgeDocumentReader.load_document([request.document.collection], request.document.id)
        settings = config.record_extraction
        long = document.text_length > settings.max_document_chars
        path = request.document.path
        if long:
            await displayer.display_thought(t("agent.record_extraction.progress.partial", path=path))
        elif document.text_length > LONG_DOCUMENT_CHARACTERS:
            await displayer.display_thought(t("agent.record_extraction.progress.reading", path=path))

        async def still_reading(minutes: int) -> None:
            await displayer.display_thought(
                t("agent.record_extraction.progress.still_reading", path=path, minutes=minutes)
            )

        llm_config = config.extraction_llm()
        async with ReadingHeartbeat.around(still_reading), llm_config.cost_reporting_llm(displayer, user=user) as llm:
            result = await RecordExtractor.extract(
                request.record_schema,
                document,
                llm,
                llm_config,
                t,
                request.instructions,
                limiter=ExtractionSlots.calls(config.agent_id, settings.max_parallel_extractions),
                max_windows=PARTIAL_READ_WINDOWS if long else None,
                row_terms=request.row_terms,
            )
        if result.failed:
            return DocumentRecordExtraction._failed(request, result.failure_reason or ""), []
        if result.partial:
            read = min(PARTIAL_READ_WINDOWS, result.window_count)
            logger.info("[record-extraction] %s read in part: %d of %d windows", path, read, result.window_count)
        rows = [record.values for record in result.records]
        return await DocumentRecordExtraction._stored(request, rows, result.partial), rows

    @staticmethod
    async def _stored(
        request: DocumentExtractionRequestedEvent, rows: list[dict[str, RecordValue]], partial: bool
    ) -> DocumentExtractedEvent:
        rows_key = (
            await ExtractionFileStore.put_rows(request.run.extraction_id, request.event_id, rows) if rows else None
        )
        unsure = sum(1 for row in rows if row.get(RecordSchema.MATCH_FIELD) == RecordSchema.MATCH_UNSURE)
        return DocumentExtractedEvent(
            run=request.run,
            request_event_id=request.event_id,
            document=request.document,
            rows_key=rows_key,
            row_count=len(rows),
            unsure_count=unsure,
            partly_read=partial,
        )

    @staticmethod
    def _failed(request: DocumentExtractionRequestedEvent, reason: str) -> DocumentExtractedEvent:
        return DocumentExtractedEvent(
            run=request.run,
            request_event_id=request.event_id,
            document=request.document,
            failure_reason=reason[:FAILURE_REASON_CHARACTERS] or "unknown",
        )

    @staticmethod
    async def _report(
        result: DocumentExtractedEvent,
        rows: list[dict[str, RecordValue]],
        done: int,
        displayer: EventDisplayer,
        t: LocaleHandler,
    ) -> None:
        count = {"done": min(done, result.run.file_count), "files": result.run.file_count, "path": result.document.path}
        if result.failure_reason is not None:
            thought = t("agent.record_extraction.progress.failed", reason=result.failure_reason, **count)
        elif rows:
            first = DocumentRecordExtraction._first_rows(rows, result.run.field_names)
            thought = t("agent.record_extraction.progress.extracted_rows", rows=result.row_count, first=first, **count)
        else:
            thought = t("agent.record_extraction.progress.extracted", rows=0, **count)
        await displayer.display_thought(thought)

    @staticmethod
    def _first_rows(rows: list[dict[str, RecordValue]], field_names: list[str]) -> str:
        """The first rows in a line each, their filled cells only, so the progress shows what the table finds."""
        lines = []
        for row in rows[:PREVIEW_ROWS_IN_PROGRESS]:
            cells = ", ".join(str(row[name]) for name in field_names if row.get(name) not in (None, ""))
            lines.append(cells if len(cells) <= PROGRESS_ROW_CHARACTERS else cells[: PROGRESS_ROW_CHARACTERS - 1] + "…")
        more = " …" if len(rows) > PREVIEW_ROWS_IN_PROGRESS else ""
        return "; ".join(lines) + more
