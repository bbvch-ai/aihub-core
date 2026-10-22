import re
from collections.abc import Sequence
from typing import Annotated

from swiss_ai_hub.core.jira.jira_invalid_query_error import JiraInvalidQueryError
from swiss_ai_hub.core.jira.jira_version import JiraVersion

_ORDER_BY = re.compile(r"\border\s+by\b", re.IGNORECASE)
_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


class JiraJql:
    """Builds the JQL a ticket search sends, so that values taken from a chat message stay values."""

    @staticmethod
    def string_literal(value: Annotated[str, "Any text, e.g. a version name read from a chat message"]) -> str:
        """A quoted JQL string: ``2.4" OR project = HR`` stays one value instead of widening the query."""
        return '"' + "".join(_ESCAPES.get(character, character) for character in value) + '"'

    @staticmethod
    def fix_version_clause(versions: Annotated[Sequence[JiraVersion], "The versions whose tickets to find"]) -> str:
        """Matches by id: a version named like a number would otherwise be read as an id, and one name in two
        projects is two versions."""
        if not versions:
            raise ValueError("A fix version clause needs at least one version.")
        return f"fixVersion in ({', '.join(str(int(version.id)) for version in versions)})"

    @classmethod
    def compose(
        cls,
        project_keys: Annotated[list[str], "Keys of the projects every ticket must belong to"],
        clauses: Annotated[Sequence[str], "JQL conditions every ticket must also match; empty ones are skipped"],
    ) -> str:
        """Each clause is parenthesised, so an ``OR`` in one cannot reach past the project restriction."""
        ordered = [clause.strip() for clause in clauses if clause.strip() and _ORDER_BY.search(clause)]
        if ordered:
            raise JiraInvalidQueryError([f"a clause must not contain ORDER BY: {clause}" for clause in ordered])
        projects = ", ".join(cls.string_literal(key) for key in project_keys)
        conditions = [f"project in ({projects})", *(f"({clause.strip()})" for clause in clauses if clause.strip())]
        return " AND ".join(conditions)
