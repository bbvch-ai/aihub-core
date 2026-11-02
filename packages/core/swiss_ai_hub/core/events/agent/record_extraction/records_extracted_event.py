from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_file import ExtractedTableFile
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RecordsExtractedEvent(ControlAndDisplayEvent):
    """
    The answer to `ExtractRecordsEvent`: a preview of the table naming the source of every row, the whole table as a
    file, and its summary.

    The event carries only the first rows; every row is in `file`, a CSV in object storage, so a table of any size
    stays out of the message broker. A blueprint that called the extraction itself shows the preview as its answer.
    When a model chose it in a tool loop (`tool_call_id` is set), the model only reads the summary, so chat clients
    show the preview themselves: OpenWebUI as a block of the answer, the OpenAI-compatible API as answer text. Clients
    offer the file for download.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.records_extracted_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.records_extracted_event.description"
    )

    extraction_id: Annotated[str, Field(description="The `ExtractRecordsEvent` this answers.")]
    columns: Annotated[list[str], Field(description="The table's columns, the source columns first.")] = []
    table: Annotated[
        str,
        Field(description="The first rows as a markdown table, a preview when `file` holds more; empty without rows."),
    ] = ""
    file: Annotated[
        ExtractedTableFile | None, Field(description="The whole table as a CSV file; none when there are no rows.")
    ] = None
    summary: Annotated[
        str, Field(description="Files matched, rows found, files that failed and why, and what was cut short.")
    ]
    file_count: Annotated[int, Field(description="Documents extracted from.", ge=0)] = 0
    failed_count: Annotated[int, Field(description="Documents that could not be extracted.", ge=0)] = 0
    row_count: Annotated[int, Field(description="Rows in the preview.", ge=0)] = 0
    total_row_count: Annotated[int, Field(description="Rows found; every one of them is in `file`.", ge=0)] = 0
    truncated: Annotated[
        bool, Field(description="Whether the search for documents stopped at a limit, so documents may be missing.")
    ] = False
    awaiting_confirmation: Annotated[
        bool,
        Field(
            description="Whether this is a sample of a selection too large to extract unasked; every document is "
            "extracted once the user confirms."
        ),
    ] = False
    tool_call_id: Annotated[
        str | None,
        Field(
            description="The tool call this answers when a model chose the extraction in a tool loop; none otherwise."
        ),
    ] = None
