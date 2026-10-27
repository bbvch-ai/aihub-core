from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria, KnowledgeDocumentSelection


class ExtractRecordsArguments(BaseModel):
    """What the model passes to preview or run an extraction: which documents, which columns, which rows."""

    any_of: Annotated[
        list[KnowledgeDocumentCriteria],
        Field(
            description="The documents to extract from: a document counts when it meets every condition of at least "
            "one entry. Use what the listing and search tools showed, e.g. a path glob and a supplier name.",
            min_length=1,
        ),
    ]
    fields: Annotated[
        str,
        Field(
            description="The table's columns in the user's words, e.g. 'invoice number, date, item, amount, currency'.",
            min_length=1,
        ),
    ]
    instructions: Annotated[
        str | None,
        Field(
            description="Which rows to keep, in the user's words, e.g. 'only hardware positions'; never a column. "
            "Words that describe the rows belong here, not in a content condition. Null when every row is wanted; "
            "never how many rows or how the table is laid out (not 'all rows' or 'one row per contract'). Only the "
            "user's condition, never findings about particular documents (not 'Acme's cap of CHF 50,000 qualifies')."
        ),
    ] = None
    row_terms: Annotated[
        str | None,
        Field(
            description="Words or a regular expression the lines holding the wanted rows usually contain, e.g. "
            "'Hardware|Laptop|Monitor|Server'. Used only to find the right parts of long documents; it never "
            "narrows which documents are selected."
        ),
    ] = None
    document_terms: Annotated[
        str | None,
        Field(
            description="Words or a regular expression the documents holding wanted rows likely contain, such as a "
            "supplier's name, e.g. 'Hooli'. Used only to choose which documents are sampled and read first; it never "
            "narrows which documents are selected."
        ),
    ] = None

    @property
    def selection(self) -> KnowledgeDocumentSelection:
        return KnowledgeDocumentSelection(any_of=self.any_of)
