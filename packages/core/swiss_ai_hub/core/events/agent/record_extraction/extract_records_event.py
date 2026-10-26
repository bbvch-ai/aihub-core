from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection import (
    KnowledgeDocumentSelection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ExtractRecordsEvent(ControlAndDisplayEvent):
    """
    Asks the record-extraction capability for one table across the selected knowledge documents.

    Built with `RecordExtraction.extract(...)`, or by the capability's tool adapter when a model chose
    `extract_records`; answered with `RecordsExtractedEvent`. The collections are the caller's, already narrowed to
    what the asking user may read, never the model's.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.extract_records_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.extract_records_event.description"
    )

    selection: Annotated[
        KnowledgeDocumentSelection | None,
        Field(description="The documents to extract from; none when the request continues a pending extraction."),
    ] = None
    continue_pending: Annotated[
        bool,
        Field(
            description="Whether to extract the next part of the extraction this conversation left pending, with "
            "its documents and columns, instead of a new selection."
        ),
    ] = False
    fields: Annotated[str, Field(description="What each row holds, in the user's words, e.g. 'date, item, amount'.")]
    instructions: Annotated[
        str | None, Field(description="Which records to keep, e.g. 'only hardware'; never turned into a column.")
    ] = None
    row_terms: Annotated[
        str | None,
        Field(
            description="Words or a regular expression the lines holding wanted records usually contain; used only "
            "to find the right parts of a long document, never to choose documents."
        ),
    ] = None
    collections: Annotated[
        list[BucketNamespacePair], Field(description="The collections the documents are selected from.")
    ]
    notices: Annotated[
        list[str], Field(description="What the caller wants said with the table's summary, e.g. ignored references.")
    ] = []
    cut_short: Annotated[
        bool, Field(description="Whether the caller stopped looking for documents at a limit before it was done.")
    ] = False
    tool_call_id: Annotated[
        str | None,
        Field(
            description="The tool call this answers when a model chose the extraction in a tool loop; none otherwise."
        ),
    ] = None
