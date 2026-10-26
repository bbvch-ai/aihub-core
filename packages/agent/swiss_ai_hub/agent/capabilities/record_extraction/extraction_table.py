import json

from swiss_ai_hub.core.events.agent import RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai import ExtractedTableMarkup, RecordSchema
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import CellValue, DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun

# Sizes are counted as the events carry them, JSON-escaped. The largest event is the blueprint's completion request:
# its stop message holds table and summary, its answer the summary, and every chat message stores its text twice. So
# 2 x table + 4 x summary must stay far below the broker's 1 MB limit, with room for the user's question.
TABLE_BYTES = 260_000
SUMMARY_BYTES = 30_000
FAILED_FILES_LISTED = 30
FAILED_LIST_BYTES = 15_000
LISTED_BYTES = 5_000
CRITERIA_CHARACTERS = 1_000
# Open WebUI re-renders a whole message on every event, so the pipe shows a tool call's table inline only up to 100
# rows and 64,000 characters (`RecordsExtractedEventHandler`). A page for a tool call stays inside that, counted the
# way the pipe counts, so every row an answer reports is on screen and the rest follows on continue.
INLINE_ROWS = 100
INLINE_CHARACTERS = 60_000


class ExtractionTable:
    """One markdown table across every document of an extraction, each row naming the file it came from, and the
    summary that says what the table holds and what it does not."""

    @staticmethod
    def assemble(
        run: ExtractionRun, results: list[DocumentExtractedEvent], max_rows: int, t: LocaleHandler
    ) -> tuple[RecordsExtractedEvent, list[str]]:
        """The table of the rows that fit one answer, and the rendered rows that did not: nothing is dropped, the
        caller keeps them for the next answer."""
        ordered = sorted(
            {result.request_event_id: result for result in results}.values(),
            key=lambda result: (
                result.document.collection.bucket_name,
                result.document.collection.namespace_name,
                result.document.path,
            ),
        )
        unsure = sum(
            1
            for result in ordered
            for row in result.rows
            if row.get(RecordSchema.MATCH_FIELD) == RecordSchema.MATCH_UNSURE
        )
        columns = ExtractionTable._columns(run, t, with_match=bool(unsure))
        found = [
            ExtractionTable._line(ExtractionTable._cells(run, result, row, t, with_match=bool(unsure)))
            for result in ordered
            for row in result.rows
        ]
        table, shown = ExtractionTable.page(columns, found, max_rows, inline=run.tool_call_id is not None)
        failed = [result for result in ordered if result.failure_reason is not None]
        extracted = RecordsExtractedEvent(
            extraction_id=run.extraction_id,
            columns=columns,
            table=table,
            summary=ExtractionTable._summary(run, ordered, failed, len(found), unsure, t),
            file_count=len(ordered),
            failed_count=len(failed),
            row_count=shown,
            total_row_count=len(found),
            truncated=any(result.rows_dropped for result in ordered) or run.cut_short,
            tool_call_id=run.tool_call_id,
        )
        return extracted, found[shown:]

    @staticmethod
    def page(columns: list[str], lines: list[str], max_rows: int, inline: bool = False) -> tuple[str, int]:
        """The first rendered rows that fit one answer, marked so later turns condense them, and how many that is.
        `inline` pages a tool call's table, which a chat client shows inside the model's answer.

        At least one row is shown whenever there is one: a row's cells are capped, so a single row always fits, and
        showing none would leave the same rows pending forever."""
        if not lines:
            return "", 0
        header = [ExtractionTable._line(columns), ExtractionTable._line(["---"] * len(columns))]
        size = sum(ExtractionTable.serialized_bytes(line) for line in header)
        characters = sum(len(line) for line in header)
        shown = 0
        for line in lines[: min(max_rows, INLINE_ROWS) if inline else max_rows]:
            size += ExtractionTable.serialized_bytes(line)
            characters += len(line) + 1
            if shown and (size > TABLE_BYTES or (inline and characters > INLINE_CHARACTERS)):
                break
            shown += 1
        return ExtractedTableMarkup.wrap("\n".join([*header, *lines[:shown]]), shown), shown

    @staticmethod
    def _columns(run: ExtractionRun, t: LocaleHandler, with_match: bool) -> list[str]:
        source = [t("agent.record_extraction.table.path"), t("agent.record_extraction.table.filename")]
        if run.show_collection:
            source.insert(0, t("agent.record_extraction.table.collection"))
        fields = [name.replace("_", " ").capitalize() for name in run.field_names]
        return [*source, *fields, *([t("agent.record_extraction.table.match")] if with_match else [])]

    @staticmethod
    def _cells(
        run: ExtractionRun,
        result: DocumentExtractedEvent,
        row: dict[str, CellValue],
        t: LocaleHandler,
        with_match: bool,
    ) -> list[str]:
        document = result.document
        filename = document.filename
        if result.partly_read:
            filename = f"{filename} {t('agent.record_extraction.table.partly_read')}"
        source = [document.path, filename]
        if run.show_collection:
            source.insert(0, f"{document.collection.bucket_name}/{document.collection.namespace_name}")
        values = [*source, *(row.get(name) for name in run.field_names)]
        if with_match:
            unsure = row.get(RecordSchema.MATCH_FIELD) == RecordSchema.MATCH_UNSURE
            values.append(t(f"agent.record_extraction.table.match_{'unsure' if unsure else 'yes'}"))
        return [ExtractionTable._cell(value) for value in values]

    @staticmethod
    def _cell(value: CellValue) -> str:
        if value is None:
            return ""
        return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()

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
        if run.criteria:
            lines.append(t(f"{key}.criteria", criteria=run.criteria))
        dropped = [
            t(f"{key}.document_rows_entry", file=result.document.path, count=result.rows_dropped)
            for result in results
            if result.rows_dropped
        ]
        if dropped:
            lines.append(t(f"{key}.document_rows_cut", files=ExtractionTable._listed(dropped, t)))
        empty = [result.document.path for result in results if not result.rows and result.failure_reason is None]
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
