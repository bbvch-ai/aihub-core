from swiss_ai_hub.core.events.agent import RecordsExtractedEvent

# The model reads the summary and only enough rows to describe the table: given most of a table, models retype it
# below the one the user is already shown, despite being told not to.
HEAD_CHARACTERS = 1_500


class RecordsToolResult:
    """What a model that chose to extract reads back: the table is shown to the user directly, so the model gets its
    summary and the first rows, and is told not to retype it."""

    @staticmethod
    def content(extracted: RecordsExtractedEvent) -> str:
        if not extracted.table:
            return f"{extracted.summary}{RecordsToolResult._left(extracted)}"
        head = RecordsToolResult._head(extracted.table)
        return (
            f"{extracted.summary}\n\nThe user already sees the full table of {extracted.row_count} rows next to your "
            "answer. Do not write a table or a list of its rows yourself: you see only its first rows, so anything you "
            "write would be incomplete or invented. Say in a few sentences what it holds and point out anything "
            "notable. Its first rows:\n"
            f"{head}{RecordsToolResult._left(extracted)}"
        )

    @staticmethod
    def _left(extracted: RecordsExtractedEvent) -> str:
        """What the extraction left for later: the user decides whether to go on, never the model on its own."""
        if not extracted.remaining_documents and not extracted.remaining_rows:
            return ""
        left = (
            f"{extracted.remaining_rows} more rows"
            if extracted.remaining_rows
            else f"{extracted.remaining_documents} more documents"
        )
        return (
            f"\n\n{left} are left for later. Ask the user whether to narrow the request or to continue; only when "
            "they agree, call extract_records with continue_pending set to true."
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
