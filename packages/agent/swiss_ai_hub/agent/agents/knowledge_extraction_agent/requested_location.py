import re
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria

# A written path is read one word at a time, never with one pattern over the whole message, which user text could make
# backtrack: a word is a path when it has a folder, ends in a file extension and is not a URL.
_WORD_BREAKS = re.compile(r"[\s()\[\]{}<>=,;\"'`|]+")
_WORD_EDGES = ":!?."
_SEGMENT = re.compile(r"[\w.\-]+")
_EXTENSION = re.compile(r"[A-Za-z0-9]{1,5}")


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
        paths = (RequestedLocation._written_path(word) for word in _WORD_BREAKS.split(message))
        return [cls(path_glob=f"**/{path}", path_regex=None) for path in dict.fromkeys(path for path in paths if path)]

    @staticmethod
    def _written_path(word: str) -> str | None:
        """The path a word spells out, without the punctuation around it or a leading slash; None for any other word."""
        if "://" in word:
            return None
        segments = word.strip(_WORD_EDGES).lstrip("/").split("/")
        if len(segments) < 2 or not all(_SEGMENT.fullmatch(segment) for segment in segments):
            return None
        stem, _, extension = segments[-1].rpartition(".")
        return "/".join(segments) if stem and _EXTENSION.fullmatch(extension) else None

    def as_criteria(self) -> KnowledgeDocumentCriteria:
        return KnowledgeDocumentCriteria(path_glob=self.path_glob, path_regex=self.path_regex)

    def describe(self) -> str:
        return " and ".join(part for part in (self.path_glob, self.path_regex) if part)
