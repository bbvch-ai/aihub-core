from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RecordsExtractedEvent(ControlAndDisplayEvent):
    """
    The answer to `ExtractRecordsEvent`: one markdown table naming the source of every row, and its summary.

    A blueprint that called the extraction itself shows the table as its answer. When a model chose it in a tool loop
    (`tool_call_id` is set), the model only reads the summary, so chat clients show the table themselves: OpenWebUI as
    a block of the answer, the OpenAI-compatible API as answer text.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.records_extracted_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.records_extracted_event.description"
    )

    extraction_id: Annotated[str, Field(description="The `ExtractRecordsEvent` this answers.")]
    columns: Annotated[list[str], Field(description="The table's columns, the source columns first.")] = []
    table: Annotated[str, Field(description="The rows as a markdown table, empty when there are none.")] = ""
    summary: Annotated[
        str, Field(description="Files matched, rows found, files that failed and why, and what was cut short.")
    ]
    file_count: Annotated[int, Field(description="Documents extracted from.", ge=0)] = 0
    failed_count: Annotated[int, Field(description="Documents that could not be extracted.", ge=0)] = 0
    row_count: Annotated[int, Field(description="Rows in the table.", ge=0)] = 0
    total_row_count: Annotated[int, Field(description="Rows found, more than the table holds when cut.", ge=0)] = 0
    truncated: Annotated[bool, Field(description="Whether the result was cut short at a limit.")] = False
    remaining_documents: Annotated[
        int,
        Field(
            description="Documents of this extraction not extracted yet, left for the user to continue with; more "
            "matched than one answer can extract.",
            ge=0,
        ),
    ] = 0
    remaining_rows: Annotated[
        int, Field(description="Rows found but not shown yet, shown first when the user continues.", ge=0)
    ] = 0
    tool_call_id: Annotated[
        str | None,
        Field(
            description="The tool call this answers when a model chose the extraction in a tool loop; none otherwise."
        ),
    ] = None
