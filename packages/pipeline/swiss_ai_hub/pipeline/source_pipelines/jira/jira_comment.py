from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.source_pipelines.jira.jira_timestamp import JiraTimestamp


class JiraComment(BaseModel):
    """One comment as the issue's file shows it.

    Restricted comments never become one: a comment limited to a role or group, or an internal Service Management
    comment, is visible to the sync's account but not to everyone who can read the knowledge database.
    """

    id: Annotated[str, Field(description="Jira's comment id; orders comments created in the same second.")]
    author: Annotated[str, Field(description="Display name of the author.")]
    created: Annotated[str, Field(description="Creation time, UTC ISO-8601.")]
    body_html: Annotated[str, Field(description="The comment as Jira renders it.")]

    @classmethod
    def from_embedded(cls, hit: dict[str, Any]) -> list[Self]:
        """The comments a search hit carries; their HTML sits apart from them, under ``renderedFields``."""
        raw = ((hit.get("fields") or {}).get("comment") or {}).get("comments") or []
        rendered = ((hit.get("renderedFields") or {}).get("comment") or {}).get("comments") or []
        html_by_id = {str(comment["id"]): comment.get("body") or "" for comment in rendered}
        return cls._public_in_order([(comment, html_by_id.get(str(comment["id"]), "")) for comment in raw])

    @classmethod
    def from_paged(cls, raw: list[dict[str, Any]]) -> list[Self]:
        """Comments read from the issue's comment endpoint with ``expand=renderedBody`` (and ``properties`` for a
        service desk)."""
        return cls._public_in_order([(comment, comment.get("renderedBody") or "") for comment in raw])

    @property
    def created_label(self) -> str:
        """``2026-10-08 08:15 UTC``: the heading a reader sees above the comment."""
        return f"{self.created[:10]} {self.created[11:16]} UTC"

    @staticmethod
    def has_more_than_embedded(hit: dict[str, Any]) -> bool:
        """A search embeds a limited number of comments per issue (20 on Cloud); the rest needs the comment endpoint."""
        comment = (hit.get("fields") or {}).get("comment") or {}
        return comment.get("total", 0) > len(comment.get("comments") or [])

    @classmethod
    def _public_in_order(cls, comments: list[tuple[dict[str, Any], str]]) -> list[Self]:
        public = [
            cls(
                id=str(raw["id"]),
                author=(raw.get("author") or {}).get("displayName") or "Unknown",
                created=JiraTimestamp.to_utc_iso(raw["created"]),
                body_html=html,
            )
            for raw, html in comments
            if cls.is_public(raw)
        ]
        return sorted(public, key=lambda comment: (comment.created, int(comment.id)))

    @staticmethod
    def is_public(raw: dict[str, Any]) -> bool:
        """Not restricted to a role or group, and not an internal service desk comment. Cloud flags the latter with
        ``jsdPublic``; Data Center only with the ``sd.public.comment`` property, which a search never returns."""
        internal = any(
            prop.get("key") == "sd.public.comment" and (prop.get("value") or {}).get("internal") is True
            for prop in raw.get("properties") or []
        )
        return not raw.get("visibility") and raw.get("jsdPublic") is not False and not internal
