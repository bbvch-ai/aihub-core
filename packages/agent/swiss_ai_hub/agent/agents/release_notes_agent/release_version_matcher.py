import difflib
import re
import unicodedata
from collections.abc import Sequence
from datetime import date
from typing import Annotated

from swiss_ai_hub.core.jira import JiraVersion

from swiss_ai_hub.agent.agents.release_notes_agent.version_match import VersionMatch
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome

_QUOTES = str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'", "´": "'", "`": "'", "“": '"', "”": '"', "„": '"'})
_SPACES = re.compile(r"\s+")
_TOKEN_EDGES = "\"'.,;:!?()[]{}<>«»"
_SUGGESTIONS = 3
_RECENT = 5


class ReleaseVersionMatcher:
    """Finds the fix version a chat message asks for among the versions of the configured projects.

    A name counts only as a whole word of the message, so "2.4" is not found in "2.4.0" while "for 2.4." names 2.4;
    a name found inside a longer one ("Beta" in "2.0 Beta") does not count either. Chat clients turn typed quotes into
    curly ones, so quotes are compared straightened.
    """

    @classmethod
    def match(
        cls,
        message: Annotated[str, "What the user asked, e.g. 'release notes for 2.4.0'"],
        versions: Annotated[Sequence[JiraVersion], "Every version of the configured projects, in Jira's order"],
    ) -> VersionMatch:
        text = cls.normalized(message)
        by_name: dict[str, list[JiraVersion]] = {}
        for version in versions:
            if cls.normalized(version.name):
                by_name.setdefault(cls.normalized(version.name), []).append(version)
        found = cls._outermost({name: cls._spans(text, name) for name in by_name})
        if len(found) == 1:
            return VersionMatch(outcome=VersionMatchOutcome.FOUND, versions=by_name[found[0]])
        if found:
            return VersionMatch(outcome=VersionMatchOutcome.SEVERAL, names=[by_name[name][0].name for name in found])
        return cls._unmatched(text, by_name, cls._recent(versions))

    @staticmethod
    def normalized(text: Annotated[str, "A message or a version name"]) -> str:
        straightened = unicodedata.normalize("NFKC", text).translate(_QUOTES)
        return _SPACES.sub(" ", straightened).strip().casefold()

    @staticmethod
    def _spans(text: str, name: str) -> list[tuple[int, int]]:
        """A name starting with a digit is also found written with a leading v, as in v2.4."""
        prefix = "v?" if name[:1].isdigit() else ""
        pattern = rf"(?<![\w.-]){prefix}{re.escape(name)}(?![\w-]|\.\w)"
        return [found.span() for found in re.finditer(pattern, text)]

    @staticmethod
    def _outermost(spans: dict[str, list[tuple[int, int]]]) -> list[str]:
        every = [(start, end, name) for name, found in spans.items() for start, end in found]
        kept = [
            (start, name)
            for start, end, name in every
            if not any(
                outer_start <= start and end <= outer_end and outer_end - outer_start > end - start
                for outer_start, outer_end, _ in every
            )
        ]
        return list(dict.fromkeys(name for _, name in sorted(kept)))

    @staticmethod
    def _unmatched(text: str, by_name: dict[str, list[JiraVersion]], recent: list[str]) -> VersionMatch:
        """The first version-like word with a close name is the one asked for; a word close to none still is."""
        words = [word for word in text.split() if any(character.isdecimal() for character in word)]
        tokens = [token for token in (word.strip(_TOKEN_EDGES) for word in words) if token]
        if not tokens:
            return VersionMatch(outcome=VersionMatchOutcome.MISSING, recent=recent)
        for token in tokens:
            close = difflib.get_close_matches(token, list(by_name), n=_SUGGESTIONS)
            if close:
                return VersionMatch(
                    outcome=VersionMatchOutcome.UNKNOWN,
                    requested=token,
                    suggestions=[by_name[name][0].name for name in close],
                    recent=recent,
                )
        return VersionMatch(outcome=VersionMatchOutcome.UNKNOWN, requested=tokens[0], recent=recent)

    @staticmethod
    def _recent(versions: Sequence[JiraVersion]) -> list[str]:
        """Latest release date first; versions without one are usually the upcoming ones, so they lead. Ties go to
        the newest id: Jira numbers versions site-wide as they are created, where its own order is per project."""
        live = [version for version in versions if not version.archived]
        live.sort(
            key=lambda version: (version.release_date or date.max, int(version.id) if version.id.isdigit() else 0),
            reverse=True,
        )
        return list(dict.fromkeys(version.name for version in live))[:_RECENT]
