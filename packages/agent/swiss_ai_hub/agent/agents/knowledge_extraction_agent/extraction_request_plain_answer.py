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
    fields: Annotated[str, Field(description="The table's columns in the user's words.")]
    instructions: Annotated[
        str | None,
        Field(
            description="Which rows to keep, in the user's words: also a supplier, a party or a period the user "
            "named, since documents are not chosen by their text. Null when every row is wanted."
        ),
    ]

    @property
    def selection(self) -> KnowledgeDocumentSelection:
        """The named places, or the whole scope when the user named none."""
        criteria = [location.as_criteria() for location in self.locations if location.path_glob or location.path_regex]
        return KnowledgeDocumentSelection(any_of=criteria or [KnowledgeDocumentCriteria()])
