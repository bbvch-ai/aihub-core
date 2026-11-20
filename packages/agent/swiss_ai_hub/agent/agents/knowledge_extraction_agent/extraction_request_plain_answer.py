from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria, KnowledgeDocumentSelection

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.requested_location import RequestedLocation


class ExtractionRequestPlainAnswer(BaseModel):
    """A chat message read as a table request without the search terms: what the reading falls back to when a model
    loops in a term list until its output is cut, since the terms only order the documents and pick the sample."""

    is_table_request: Annotated[
        bool,
        Field(
            description="True when the message asks for records collected from the documents, a question the "
            "documents answer included, or confirms the sample of one; false for anything else, such as a greeting or "
            "a question about the agent."
        ),
    ]
    confirms_sample: Annotated[
        bool,
        Field(
            description="True only when a sample awaits confirmation and the message agrees to extract all of it, "
            "e.g. 'yes', 'go on', 'ja'; false for a new or changed request."
        ),
    ]
    locations: Annotated[
        list[RequestedLocation],
        Field(description="The folders, files or years the user named; empty when the whole scope is meant."),
    ]
    fields: Annotated[
        str,
        Field(
            description="The table's columns in the user's words: the value of each record, never the result of a "
            "calculation over the records."
        ),
    ]
    document_condition: Annotated[
        str | None,
        Field(
            description="Which documents count, in the user's words: a condition the whole document meets or fails, "
            "such as its supplier or party, its number, its status or version, or the period that dates it, e.g. "
            "'contracts with Hooli', 'only signed versions'. A period is written as explicit dates, e.g. 'Q4 2018' as "
            "'dated between 1 October 2018 and 31 December 2018'. Null when every document at the locations counts, "
            "when a location already expresses the period exactly, or when the rows carry the value themselves."
        ),
    ] = None
    instructions: Annotated[
        str | None,
        Field(
            description="Which rows to keep, in the user's words: the kind of row or a condition on a row's values, "
            "e.g. 'only hardware positions', also a supplier, party or date the rows carry themselves, as on a "
            "statement. A condition on the whole document goes into document_condition. Null when every row is "
            "wanted."
        ),
    ]
    calculation: Annotated[
        str | None,
        Field(
            description="The sum, average, count, maximum or comparison the user asked for over the rows, in the "
            "user's words; null when none. The agent lists the values and does not calculate."
        ),
    ]
    document_kind: Annotated[
        str | None,
        Field(
            description="The kind of document the wanted rows stand in, in a few words, e.g. 'supplier invoice with "
            "line items'; no amounts, dates or thresholds. Null when the request does not say."
        ),
    ]

    @property
    def selection(self) -> KnowledgeDocumentSelection:
        """The named places, or the whole scope when the user named none."""
        criteria = [location.as_criteria() for location in self.locations if location.path_glob or location.path_regex]
        return KnowledgeDocumentSelection(any_of=criteria or [KnowledgeDocumentCriteria()])
