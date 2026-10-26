import re
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria

# A path with at least one folder and a file extension, not part of a URL or a longer path; a leading slash is dropped.
_WRITTEN_PATH = re.compile(r"(?<![\w:/.\-])/?((?:[\w.\-]+/)+[\w\-]+(?:\.[\w\-]+)*\.[A-Za-z0-9]{1,5})(?![\w/])")


class RequestedLocation(BaseModel):
    """A place in the collections the user named: a folder, a file or a year in the path. Never what the documents
    say, since only reading every document can tell which ones hold the wanted rows."""

    path_glob: Annotated[str | None, Field(description="Glob on the path, e.g. 'contracts/**' or 'invoices/2025/**'.")]
    path_regex: Annotated[str | None, Field(description="Regular expression searched anywhere in the path.")]

    @classmethod
    def written_in(cls, message: Annotated[str, "The user's message"]) -> list[Self]:
        """The file paths the message spells out, matched as the end of a document's path, since a user often writes
        only its last folders. A model may read such a path as a topic and extract from the whole scope, which puts a
        file of the same name in place of the one asked for; a written path is never a topic."""
        return [cls(path_glob=f"**/{path}", path_regex=None) for path in dict.fromkeys(_WRITTEN_PATH.findall(message))]

    def as_criteria(self) -> KnowledgeDocumentCriteria:
        return KnowledgeDocumentCriteria(path_glob=self.path_glob, path_regex=self.path_regex)

    def describe(self) -> str:
        return " and ".join(part for part in (self.path_glob, self.path_regex) if part)
