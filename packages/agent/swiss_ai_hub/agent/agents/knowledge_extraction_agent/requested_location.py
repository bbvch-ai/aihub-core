import re
from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import (
    KnowledgeDocumentCriteria,
    NormalizedDate,
    PathDateParser,
    PathDateRange,
    PathDateVerdict,
)

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
_PATTERN_CHARACTERS = frozenset("*?[]{}")
# A pattern segment is dated as no folder at all, so `2025*/q1` never dates its child either.
_PATTERN_STAND_IN = "*"
_EVERYWHERE = "**"


class RequestedLocation(BaseModel):
    """A place in the collections the user named: a folder or a file. Never what the documents say, since only reading
    every document can tell which ones hold the wanted rows."""

    path_glob: Annotated[str | None, Field(description="Glob on the path, e.g. 'contracts/**' or 'invoices/**'.")]
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

    @property
    def is_everywhere(self) -> bool:
        """A glob that matches every path; a leading slash is stripped from every glob before matching."""
        return self.path_glob is not None and self.path_glob.lstrip("/") == _EVERYWHERE and self.path_regex is None

    def without_period_folders(
        self,
        period: Annotated[PathDateRange, "The period the request dates the documents in"],
        message: Annotated[str, "What the user wrote, every turn of it"],
    ) -> Self:
        """The glob without the date folders that only repeat the period: a model reads "invoice totals 2025" as
        invoices/2025/** although the period already dates the documents, and the folder then leaves out every
        undated invoice. Each such folder becomes `**`, so the glob only ever matches more. A folder dated outside or
        across the period, one that names more than a date, or one the message writes as a path is the user's choice
        and stays; a regex is never read."""
        if self.path_glob is None or self.path_regex is not None:
            return self
        segments = self.path_glob.split("/")
        literal = [_PATTERN_STAND_IN if _PATTERN_CHARACTERS & set(segment) else segment for segment in segments]
        dates = PathDateParser.folder_dates(literal)
        text = message.casefold().replace("\\", "/")
        repeated = RequestedLocation._repeating(segments, dates, period, text)
        if not repeated:
            return self
        kept = [_EVERYWHERE if index in repeated else segment for index, segment in enumerate(segments)]
        merged = [
            segment for index, segment in enumerate(kept) if not (index and segment == kept[index - 1] == _EVERYWHERE)
        ]
        return self.model_copy(update={"path_glob": "/".join(merged)})

    @staticmethod
    def _repeating(
        segments: list[str], dates: list[NormalizedDate | None], period: PathDateRange, text: str
    ) -> set[int]:
        """The folders of each run of date folders that reads as one date within the period, such as 2025/q1 for Q1
        2025, and that the message does not write as a path. A run is judged whole: the year above a quarter repeats
        the period as much as the quarter does, and keeping it would still leave out the undated documents."""
        repeated: set[int] = set()
        for run in RequestedLocation._date_runs(dates):
            innermost = dates[run[-1]]
            if innermost is None or period.verdict_of(innermost) is not PathDateVerdict.WITHIN:
                continue
            nested = all(
                (dated := dates[index]) is not None and dated.start <= innermost.start and innermost.end <= dated.end
                for index in run
            )
            if nested and not RequestedLocation._writes_as_path(run, segments, text):
                repeated.update(run)
        return repeated

    @staticmethod
    def _date_runs(dates: list[NormalizedDate | None]) -> list[list[int]]:
        runs: list[list[int]] = []
        for index, dated in enumerate(dates):
            if dated is not None and runs and runs[-1][-1] == index - 1:
                runs[-1].append(index)
            elif dated is not None:
                runs.append([index])
        return runs

    @staticmethod
    def _writes_as_path(run: list[int], segments: list[str], text: str) -> bool:
        """Whether the message writes a folder of the run as a path, next to a folder before or after it."""
        first, last = max(run[0] - 1, 0), min(run[-1], len(segments) - 2)
        pairs = ("/".join(segments[index : index + 2]) for index in range(first, last + 1))
        return any(pair.casefold() in text for pair in pairs)

    def as_criteria(self) -> KnowledgeDocumentCriteria:
        return KnowledgeDocumentCriteria(path_glob=self.path_glob, path_regex=self.path_regex)

    def describe(self) -> str:
        return " and ".join(part for part in (self.path_glob, self.path_regex) if part)
