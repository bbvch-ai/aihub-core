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
# A name typed without its extension counts only when it could not be an ordinary word of the request.
_DISTINCTIVE_STEM_LENGTH = 4
_DISTINCTIVE_STEM_CHARACTERS = frozenset("_-.0123456789")
_GLOB_CHARACTERS = {"*": "[*]", "?": "[?]", "[": "[[]"}


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

    @classmethod
    def named_in(
        cls,
        message: Annotated[str, "The user's message"],
        paths: Annotated[list[str], "Paths of the documents in scope"],
    ) -> list[Self]:
        """The documents in scope whose file name the message holds, with or without its extension: users name a file
        far more often than they write its folders. Matched against the real names, so no word is taken for a file that
        does not exist; a name shared by files in several folders names all of them."""
        text = message.casefold()
        names = dict.fromkeys(path.rsplit("/", 1)[-1] for path in paths)
        named = [name for name in names if RequestedLocation._holds_name(text, name) and "{" not in name]
        return [cls(path_glob=f"**/{RequestedLocation._literal_glob(name)}", path_regex=None) for name in named]

    @staticmethod
    def _holds_name(text: str, name: str) -> bool:
        stem, dot, _ = name.rpartition(".")
        spellings = [name.casefold()]
        if dot and len(stem) >= _DISTINCTIVE_STEM_LENGTH and _DISTINCTIVE_STEM_CHARACTERS & set(stem):
            spellings.append(stem.casefold())
        return any(RequestedLocation._occurs_alone(text, spelling) for spelling in spellings)

    @staticmethod
    def _occurs_alone(text: str, spelling: str) -> bool:
        """Whether the spelling occurs as a whole name: not inside a longer word and not as the end of a written path,
        which `written_in` already reads with its folders, and not followed by another extension."""
        start = text.find(spelling)
        while start >= 0:
            end = start + len(spelling)
            before = text[start - 1] if start else " "
            after = text[end : end + 2].ljust(2)
            ends_word = not (after[0].isalnum() or after[0] in "_-") and not (after[0] == "." and after[1].isalnum())
            if ends_word and not (before.isalnum() or before in "_/\\"):
                return True
            start = text.find(spelling, start + 1)
        return False

    @staticmethod
    def _literal_glob(name: str) -> str:
        return "".join(_GLOB_CHARACTERS.get(character, character) for character in name)

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
