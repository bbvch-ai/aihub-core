import asyncio
import json

from swiss_ai_hub.core.events.agent import RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import ExtractedTableMarkup, ExtractionFileStore, RecordSchema, RecordValue
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun

# Every row is in the CSV file; the event carries a preview. Open WebUI re-renders a whole message on every event, so
# the preview stays within what the pipe shows inline (100 rows, 64,000 characters), and its JSON-escaped size (every
# non-ASCII character six bytes) stays far below the broker's 1 MB limit, also where an answer carries it twice.
PREVIEW_ROWS = 100
PREVIEW_CHARACTERS = 60_000
PREVIEW_BYTES = 150_000
# A preview cell holds at most this much of a long value, such as a whole clause, marked so the reader sees the cut;
# the file keeps it whole.
CELL_CHARACTERS = 1_000
CELL_CUT_MARK = "…"
SUMMARY_BYTES = 30_000
FAILED_FILES_LISTED = 30
FAILED_LIST_BYTES = 15_000
LISTED_BYTES = 5_000
CRITERIA_CHARACTERS = 1_000
# Row files are read side by side, a bounded number at once, so a thousand documents neither run one by one nor open
# a thousand connections.
ROW_FILES_AT_ONCE = 16


class ExtractionTable:
    """One table across every document of an extraction, each row naming the file it came from: stored whole as a CSV
    file, previewed on the event, with the summary that says what the table holds and what it does not."""

    @staticmethod
    async def assemble(
        run: ExtractionRun, results: list[DocumentExtractedEvent], t: LocaleHandler
    ) -> RecordsExtractedEvent:
        ordered = sorted(
            {result.request_event_id: result for result in results}.values(),
            key=lambda result: (
                result.document.collection.bucket_name,
                result.document.collection.namespace_name,
                result.document.path,
            ),
        )
        unsure = sum(result.unsure_count for result in ordered)
        columns = ExtractionTable._columns(run, t, with_match=bool(unsure))
        rows = await ExtractionTable._rows(ordered)
        found = [
            ExtractionTable._values(run, result, row, t, with_match=bool(unsure))
            for result, document_rows in zip(ordered, rows, strict=True)
            for row in document_rows
        ]
        table, shown = ExtractionTable.preview(columns, found)
        failed = [result for result in ordered if result.failure_reason is not None]
        stored = (
            await ExtractionFileStore.put_table(run.extraction_id, ExtractionTable._filename(run), columns, found)
            if found
            else None
        )
        return RecordsExtractedEvent(
            extraction_id=run.extraction_id,
            columns=columns,
            table=table,
            file=stored,
            summary=ExtractionTable._summary(run, ordered, failed, len(found), shown, unsure, t),
            file_count=len(ordered),
            failed_count=len(failed),
            row_count=shown,
            total_row_count=len(found),
            truncated=run.cut_short,
            awaiting_confirmation=run.sample and not run.above_ceiling,
            tool_call_id=run.tool_call_id,
        )

    @staticmethod
    async def _rows(results: list[DocumentExtractedEvent]) -> list[list[dict[str, RecordValue]]]:
        limit = asyncio.Semaphore(ROW_FILES_AT_ONCE)

        async def load(result: DocumentExtractedEvent) -> list[dict[str, RecordValue]]:
            if result.rows_key is None:
                return []
            async with limit:
                return await ExtractionFileStore.rows(result.rows_key)

        return list(await asyncio.gather(*(load(result) for result in results)))

    @staticmethod
    def _filename(run: ExtractionRun) -> str:
        return f"table-{run.extraction_id}.csv"

    @staticmethod
    def preview(columns: list[str], rows: list[list[RecordValue]]) -> tuple[str, int]:
        """The first rows as a markdown table within the preview's limits, marked so later turns condense it, and how
        many that is. At least one row is shown whenever there is one: cells are capped, so a single row always fits."""
        if not rows:
            return "", 0
        header = [ExtractionTable._line(columns), ExtractionTable._line(["---"] * len(columns))]
        size = sum(ExtractionTable.serialized_bytes(line) for line in header)
        characters = sum(len(line) + 1 for line in header)
        lines: list[str] = []
        for row in rows[:PREVIEW_ROWS]:
            line = ExtractionTable._line([ExtractionTable._cell(value) for value in row])
            size += ExtractionTable.serialized_bytes(line)
            characters += len(line) + 1
            if lines and (size > PREVIEW_BYTES or characters > PREVIEW_CHARACTERS):
                break
            lines.append(line)
        return ExtractedTableMarkup.wrap("\n".join([*header, *lines]), len(lines)), len(lines)

    @staticmethod
    def _columns(run: ExtractionRun, t: LocaleHandler, with_match: bool) -> list[str]:
        source = [t("agent.record_extraction.table.path"), t("agent.record_extraction.table.filename")]
        if run.show_collection:
            source.insert(0, t("agent.record_extraction.table.collection"))
        fields = [name.replace("_", " ").capitalize() for name in run.field_names]
        return [*source, *fields, *([t("agent.record_extraction.table.match")] if with_match else [])]

    @staticmethod
    def _values(
        run: ExtractionRun,
        result: DocumentExtractedEvent,
        row: dict[str, RecordValue],
        t: LocaleHandler,
        with_match: bool,
    ) -> list[RecordValue]:
        document = result.document
        filename = document.filename
        if result.partly_read:
            filename = f"{filename} {t('agent.record_extraction.table.partly_read')}"
        source: list[RecordValue] = [document.path, filename]
        if run.show_collection:
            source.insert(0, f"{document.collection.bucket_name}/{document.collection.namespace_name}")
        values = [*source, *(row.get(name) for name in run.field_names)]
        if with_match:
            unsure = row.get(RecordSchema.MATCH_FIELD) == RecordSchema.MATCH_UNSURE
            values.append(t(f"agent.record_extraction.table.match_{'unsure' if unsure else 'yes'}"))
        return values

    @staticmethod
    def _cell(value: RecordValue) -> str:
        if value is None:
            return ""
        text = str(value)
        if len(text) > CELL_CHARACTERS:
            text = text[: CELL_CHARACTERS - len(CELL_CUT_MARK)] + CELL_CUT_MARK
        return text.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()

    @staticmethod
    def serialized_bytes(line: str) -> int:
        """The bytes a line adds to an event's JSON as events are serialized (`BaseEvent.model_dump_json`: every
        non-ASCII character escaped to six bytes), without the quotes, plus its escaped line break."""
        return len(json.dumps(line)) - 2 + len("\\n")

    @staticmethod
    def _line(cells: list[str]) -> str:
        return f"| {' | '.join(cells)} |"

    @staticmethod
    def _summary(
        run: ExtractionRun,
        results: list[DocumentExtractedEvent],
        failed: list[DocumentExtractedEvent],
        found: int,
        shown: int,
        unsure: int,
        t: LocaleHandler,
    ) -> str:
        key = "agent.record_extraction.summary"
        if run.sample:
            counted = "sample_counts_ceiling" if run.above_ceiling else "sample_counts"
            counts = t(f"{key}.{counted}", files=len(results), total=run.total_documents, rows=found)
        else:
            counts = t(f"{key}.counts", files=len(results), rows=found, failed=len(failed))
        lines = [counts]
        if shown < found:
            lines.append(t(f"{key}.preview", shown=shown, rows=found))
        if run.criteria:
            lines.append(t(f"{key}.criteria", criteria=run.criteria))
        empty = [result.document.path for result in results if not result.row_count and result.failure_reason is None]
        if empty:
            lines.append(t(f"{key}.no_rows", files=ExtractionTable._listed(empty, t)))
        if unsure:
            lines.append(t(f"{key}.unsure", count=unsure))
        partly_read = [result.document.path for result in results if result.partly_read]
        if partly_read:
            lines.append(t(f"{key}.partly_read", files=ExtractionTable._listed(partly_read, t)))
        lines.extend(run.notices)
        if failed:
            lines.append(ExtractionTable._failed_files(failed, t))
        return ExtractionTable.capped("\n\n".join(lines))

    @staticmethod
    def _listed(entries: list[str], t: LocaleHandler) -> str:
        """The first entries, as many as fit, and how many more there are, so a long list never hides that it was
        shortened."""
        listed: list[str] = []
        size = 0
        for entry in entries[:FAILED_FILES_LISTED]:
            size += ExtractionTable.serialized_bytes(entry)
            if size > LISTED_BYTES and listed:
                break
            listed.append(entry)
        if len(listed) == len(entries):
            return ", ".join(listed)
        more = t("agent.record_extraction.summary.listed_more", count=len(entries) - len(listed))
        return f"{', '.join(listed)}, {more}"

    @staticmethod
    def _failed_files(failed: list[DocumentExtractedEvent], t: LocaleHandler) -> str:
        """The failed files with their reasons, as many as fit, and how many more there are."""
        key = "agent.record_extraction.summary"
        listed: list[str] = []
        size = 0
        for result in failed[:FAILED_FILES_LISTED]:
            entry = f"- {result.document.path}: {result.failure_reason}"
            size += ExtractionTable.serialized_bytes(entry)
            if size > FAILED_LIST_BYTES:
                break
            listed.append(entry)
        if len(listed) < len(failed):
            listed.append(t(f"{key}.failed_more", count=len(failed) - len(listed)))
        return f"{t(f'{key}.failed_files')}\n\n" + "\n".join(listed)

    @staticmethod
    def capped(summary: str) -> str:
        """The summary within its share of the largest event; only notices from a model can make it this long."""
        while ExtractionTable.serialized_bytes(summary) > SUMMARY_BYTES:
            summary = summary[: int(len(summary) * 0.9)].rstrip() + "…"
        return summary
