import json
import logging

from redis.asyncio import Redis
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentReader, RecordExtractor
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import CellValue, DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.document_extraction_requested_event import (
    DocumentExtractionRequestedEvent,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_slots import ExtractionSlots
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields

logger = logging.getLogger(__name__)

# Every event must stay far below the message broker's limit (1 MB in development): an oversized event is lost
# silently and the join then waits forever. A cell is cut first, marked so the reader sees it, then rows are left out
# of the event. Cells hold whole contract clauses, so they may be long; the event's size is measured as serialized.
CELL_CHARACTERS = 1_000
CELL_CUT_MARK = "…"
EVENT_BYTES = 200_000
FAILURE_REASON_CHARACTERS = 300
# Parts of a document longer than the profile's full-read limit that are read: its opening and the parts most likely
# to hold wanted lines (see `WindowSelection`).
PARTIAL_READ_WINDOWS = 12
# The running count of an extraction's finished documents, for the progress the chat shows; kept briefly in Valkey
# because the documents finish in separate steps, possibly on separate replicas.
_DONE_KEY = "record_extraction:{extraction_id}:done"
_DONE_TTL_SECONDS = 3600


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
        async with ExtractionSlots.documents(config.agent_id, settings.max_parallel_extractions):
            try:
                result = await DocumentRecordExtraction._extract(request, config, displayer, t, user)
            except Exception as error:
                logger.exception("[record-extraction] %s failed", request.document.path)
                result = DocumentRecordExtraction._failed(request, f"{type(error).__name__}: {error}")
        await DocumentRecordExtraction._report(
            result, await DocumentRecordExtraction._done(result, redis), displayer, t
        )
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
    ) -> DocumentExtractedEvent:
        document = await KnowledgeDocumentReader.load_document([request.document.collection], request.document.id)
        settings = config.record_extraction
        long = document.text_length > settings.max_document_chars
        if long:
            await displayer.display_thought(t("agent.record_extraction.progress.partial", path=request.document.path))
        llm_config = config.extraction_llm()
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
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
            return DocumentRecordExtraction._failed(request, result.failure_reason or "")
        if result.partial:
            read = min(PARTIAL_READ_WINDOWS, result.window_count)
            logger.info(
                "[record-extraction] %s read in part: %d of %d windows",
                request.document.path,
                read,
                result.window_count,
            )
        extracted = DocumentRecordExtraction._bounded(request, [record.values for record in result.records])
        return extracted.model_copy(update={"partly_read": result.partial})

    @staticmethod
    def _bounded(request: DocumentExtractionRequestedEvent, rows: list[dict[str, CellValue]]) -> DocumentExtractedEvent:
        """The document's rows, as many as fit the event: the size counts the event as `BaseEvent.model_dump_json`
        writes it (non-ASCII escaped), run and document included, so umlauts and long criteria cannot push it past the
        broker's limit."""
        event = DocumentExtractedEvent(run=request.run, request_event_id=request.event_id, document=request.document)
        size = len(event.model_dump_json().encode())
        kept: list[dict[str, CellValue]] = []
        for row in rows:
            cut = {name: DocumentRecordExtraction._cell(value) for name, value in row.items()}
            size += len(json.dumps(cut)) + len(", ")
            if size > EVENT_BYTES:
                return event.model_copy(update={"rows": kept, "rows_dropped": len(rows) - len(kept)})
            kept.append(cut)
        return event.model_copy(update={"rows": kept})

    @staticmethod
    def _cell(value: CellValue) -> CellValue:
        if isinstance(value, str) and len(value) > CELL_CHARACTERS:
            return value[: CELL_CHARACTERS - len(CELL_CUT_MARK)] + CELL_CUT_MARK
        return value

    @staticmethod
    def _failed(request: DocumentExtractionRequestedEvent, reason: str) -> DocumentExtractedEvent:
        return DocumentExtractedEvent(
            run=request.run,
            request_event_id=request.event_id,
            document=request.document,
            failure_reason=reason[:FAILURE_REASON_CHARACTERS] or "unknown",
        )

    @staticmethod
    async def _report(result: DocumentExtractedEvent, done: int, displayer: EventDisplayer, t: LocaleHandler) -> None:
        count = {"done": min(done, result.run.file_count), "files": result.run.file_count, "path": result.document.path}
        if result.failure_reason is not None:
            thought = t("agent.record_extraction.progress.failed", reason=result.failure_reason, **count)
        else:
            thought = t("agent.record_extraction.progress.extracted", rows=len(result.rows), **count)
        await displayer.display_thought(thought)
