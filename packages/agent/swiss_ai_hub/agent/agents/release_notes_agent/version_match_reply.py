from collections.abc import Sequence
from typing import Annotated

from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.release_notes_agent.version_match import VersionMatch
from swiss_ai_hub.agent.agents.release_notes_agent.version_match_outcome import VersionMatchOutcome

_KEY = "agent.release_notes_agent.messages"


class VersionMatchReply:
    """What to tell a user whose message names no release, several, or one Jira does not have."""

    @staticmethod
    def message(
        match: Annotated[VersionMatch, "A match that is not FOUND"],
        projects: Annotated[Sequence[str], "Keys of the configured projects"],
        t: Annotated[LocaleHandler, "Translations in the run's language"],
    ) -> str:
        """Offers the names closest to what was asked, else the newest versions, so the user can answer with one."""
        in_projects = ", ".join(projects)
        recent = ", ".join(match.recent)
        match match.outcome:
            case VersionMatchOutcome.SEVERAL:
                return t(f"{_KEY}.version_several", names=", ".join(match.names))
            case VersionMatchOutcome.UNKNOWN if match.suggestions:
                suggestions = ", ".join(match.suggestions)
                return t(
                    f"{_KEY}.version_unknown", requested=match.requested, projects=in_projects, suggestions=suggestions
                )
            case VersionMatchOutcome.UNKNOWN if match.recent:
                return t(
                    f"{_KEY}.version_unknown_recent", requested=match.requested, projects=in_projects, recent=recent
                )
            case VersionMatchOutcome.UNKNOWN:
                return t(f"{_KEY}.version_unknown_no_versions", requested=match.requested, projects=in_projects)
            case VersionMatchOutcome.MISSING if match.recent:
                return t(f"{_KEY}.version_missing", recent=recent)
            case VersionMatchOutcome.MISSING:
                return t(f"{_KEY}.version_missing_no_versions", projects=in_projects)
            case VersionMatchOutcome.FOUND:
                raise ValueError(f"{match.name} was found; there is nothing to ask the user.")
