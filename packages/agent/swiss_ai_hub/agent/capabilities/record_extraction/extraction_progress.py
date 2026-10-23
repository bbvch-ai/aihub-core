from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.extraction_estimate import ExtractionEstimate
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.capabilities.record_extraction.pending_extraction import PendingExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

_SUMMARY = "agent.record_extraction.summary"


class ExtractionProgress:
    """What an answer leaves for the next one, and how the answer says so.

    An extraction larger than one answer runs in parts, and rows beyond what one answer shows wait for the next. After
    every table this records what is left in the conversation's `PendingExtraction` and ends the summary with how to
    go on; when nothing is left it gives the totals and forgets the extraction.
    """

    @staticmethod
    async def record(
        run: ExtractionRun,
        extracted: RecordsExtractedEvent,
        overflow: list[str],
        config: RecordExtractionFields,
        thread: ThreadContext,
        t: LocaleHandler,
    ) -> RecordsExtractedEvent:
        if run.sample:
            pending = await PendingExtraction.load(thread)
            return extracted.model_copy(update={"remaining_documents": pending.remaining_documents if pending else 0})
        pending = await PendingExtraction.load(thread) if run.part else None
        if pending is None and not overflow:
            return extracted
        pending = pending or PendingExtraction(
            extraction_id=run.extraction_id,
            criteria=run.criteria,
            collections=run.collections,
            show_collection=run.show_collection,
        )
        pending = pending.model_copy(
            update={
                "columns": extracted.columns,
                "overflow_rows": overflow,
                "extracted_files": pending.extracted_files + extracted.file_count,
                "rows_found": pending.rows_found + extracted.total_row_count,
                "failed_files": pending.failed_files + extracted.failed_count,
            }
        )
        if run.part:
            pending = pending.finishing(run.part - 1)
        lines = [t(f"{_SUMMARY}.part", **ExtractionProgress._part_range(run))] if run.part else []
        return await ExtractionProgress._next(extracted, pending, lines, config, thread, t)

    @staticmethod
    async def skipped(
        answer: RecordsExtractedEvent,
        pending: PendingExtraction,
        config: RecordExtractionFields,
        thread: ThreadContext,
        t: LocaleHandler,
    ) -> RecordsExtractedEvent:
        """A part with no document left to extract still ends with what is left, or with the totals."""
        return await ExtractionProgress._next(answer, pending, [], config, thread, t)

    @staticmethod
    async def more_rows(
        request: ExtractRecordsEvent,
        pending: PendingExtraction,
        config: RecordExtractionFields,
        thread: ThreadContext,
        t: LocaleHandler,
    ) -> RecordsExtractedEvent:
        """The next rows an earlier answer found but could not show, before any further document is extracted."""
        table, shown = ExtractionTable.page(
            pending.columns,
            pending.overflow_rows,
            config.record_extraction.max_rows,
            inline=request.tool_call_id is not None,
        )
        pending = pending.model_copy(update={"overflow_rows": pending.overflow_rows[shown:]})
        extracted = RecordsExtractedEvent(
            extraction_id=request.event_id,
            columns=pending.columns,
            table=table,
            summary="\n\n".join([t(f"{_SUMMARY}.more_rows"), *request.notices]),
            row_count=shown,
            total_row_count=shown,
            tool_call_id=request.tool_call_id,
        )
        return await ExtractionProgress._next(extracted, pending, [], config, thread, t)

    @staticmethod
    async def _next(
        extracted: RecordsExtractedEvent,
        pending: PendingExtraction,
        lines: list[str],
        config: RecordExtractionFields,
        thread: ThreadContext,
        t: LocaleHandler,
    ) -> RecordsExtractedEvent:
        if pending.overflow_rows:
            lines.append(t(f"{_SUMMARY}.rows_follow", count=len(pending.overflow_rows)))
        elif pending.remaining_documents and pending.following_part is not None:
            following = pending.part(pending.following_part)
            parallel = config.record_extraction.max_parallel_extractions
            minutes = ExtractionEstimate.minutes(following, parallel)
            lines.append(t(f"{_SUMMARY}.continue_parts", files=len(following), minutes=minutes))
        elif pending.part_count > 1:
            lines.append(ExtractionProgress._totals(pending, t))
        if pending.overflow_rows or pending.remaining_documents:
            await pending.save(thread)
        else:
            await PendingExtraction.clear(thread)
        return extracted.model_copy(
            update={
                "summary": ExtractionTable.capped("\n\n".join([extracted.summary, *lines])),
                "remaining_documents": pending.remaining_documents,
                "remaining_rows": len(pending.overflow_rows),
            }
        )

    @staticmethod
    def _totals(pending: PendingExtraction, t: LocaleHandler) -> str:
        """The last part's totals, counting only documents some part extracted: one left out stays visible."""
        total = len(pending.documents)
        counts = {
            "total": total,
            "parts": pending.part_count,
            "rows": pending.rows_found,
            "files": pending.failed_files,
        }
        if pending.extracted_files >= total:
            return t(f"{_SUMMARY}.done", **counts)
        return t(f"{_SUMMARY}.done_short", extracted=pending.extracted_files, **counts)

    @staticmethod
    def _part_range(run: ExtractionRun) -> dict[str, int]:
        return {
            "part": run.part,
            "parts": run.parts,
            "first": run.first_document,
            "last": run.first_document + run.file_count - 1,
            "total": run.total_documents,
        }
