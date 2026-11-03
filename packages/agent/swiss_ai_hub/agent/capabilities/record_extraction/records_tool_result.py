from swiss_ai_hub.core.events.agent import RecordsExtractedEvent

# The model reads the summary and only enough rows to describe the table: given most of a table, models retype it
# below the one the user is already shown, despite being told not to.
HEAD_CHARACTERS = 1_500


class RecordsToolResult:
    """What a model that chose to extract reads back: the table is shown to the user directly, with the whole of it as
    a file, so the model gets its summary and the first rows, and is told not to retype it."""

    @staticmethod
    def content(extracted: RecordsExtractedEvent) -> str:
        if not extracted.table:
            return f"{extracted.summary}{RecordsToolResult._left(extracted)}"
        head = RecordsToolResult._head(extracted.table)
        return (
            f"{extracted.summary}\n\nThe user already sees the table next to your answer, the first "
            f"{extracted.row_count} of its {extracted.total_row_count} rows, and can download all of them"
            f"{RecordsToolResult._file(extracted)}. Do not write a table or a list of its rows yourself: you see only "
            "its first rows, so anything you write would be incomplete or invented. Say in a few sentences what it "
            "holds and point out anything notable. Its first rows:\n"
            f"{head}{RecordsToolResult._left(extracted)}"
        )

    @staticmethod
    def _file(extracted: RecordsExtractedEvent) -> str:
        return f" as {extracted.file.filename}" if extracted.file else ""

    @staticmethod
    def _left(extracted: RecordsExtractedEvent) -> str:
        """A sample: the user decides whether to extract everything, never the model on its own."""
        if not extracted.awaiting_confirmation:
            return ""
        return (
            "\n\nThis is only a sample of the selection. Ask the user whether to extract every document or to narrow "
            "the request; only when they agree, call extract_records with confirm_sample set to true."
        )

    @staticmethod
    def _head(table: str) -> str:
        lines = [line for line in table.splitlines() if line.startswith("|")]
        kept: list[str] = []
        size = 0
        for line in lines:
            size += len(line) + 1
            if size > HEAD_CHARACTERS:
                kept.append("| … |")
                break
            kept.append(line)
        return "\n".join(kept)
