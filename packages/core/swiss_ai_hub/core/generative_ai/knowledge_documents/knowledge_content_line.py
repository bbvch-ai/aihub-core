from typing import Annotated, Self

from pydantic import BaseModel, Field


class KnowledgeContentLine(BaseModel):
    """One line of a document's parsed text that matched, located so it can be read again in context.

    `start` and `end` are offsets into the stored text, the same ones `load_document` takes, so a caller can read the
    surrounding passage with a character range.
    """

    line_number: Annotated[int, Field(description="1-based line number in the parsed text")]
    start: Annotated[int, Field(description="Offset of the first returned character in the parsed text")]
    end: Annotated[int, Field(description="Offset one past the last returned character in the parsed text")]
    text: Annotated[str, Field(description="The line, or a window of it around the match when the line is too long")]
    clipped: Annotated[bool, Field(description="Whether `text` is only part of the line")]

    @classmethod
    def from_text(
        cls,
        text: str,
        line_start: int,
        line_end: int,
        line_number: int,
        match_start: int,
        max_chars: int,
    ) -> Self:
        """Clip a long line to a window with a quarter of it before the match, showing what leads up to it."""
        if line_end - line_start <= max_chars:
            start, end = line_start, line_end
        else:
            start = max(line_start, min(match_start - max_chars // 4, line_end - max_chars))
            end = start + max_chars
        return cls(
            line_number=line_number,
            start=start,
            end=end,
            text=text[start:end],
            clipped=(start, end) != (line_start, line_end),
        )
