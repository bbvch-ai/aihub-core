from datetime import datetime
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.jira import JiraHtml

from swiss_ai_hub.pipeline.source_pipelines.jira.jira_comment import JiraComment
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_timestamp import JiraTimestamp
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

_REST_PATH = "/rest/api/"


class JiraIssue(BaseModel):
    """One Jira issue as the sync yields it: the fields its file shows, read from a search hit.

    It carries the site URL Jira reports in the hit itself, so links in the file point where users open Jira even when
    the pipeline reaches it under another host name, and turning it into a file needs nothing but the issue.
    """

    id: Annotated[str, Field(description="Jira's issue id, stable when the issue is moved and its key changes.")]
    key: Annotated[str, Field(description="Issue key, e.g. ABC-123; its project prefix is the namespace.")]
    site: Annotated[str, Field(description="Jira's base URL as Jira reports it, including any context path.")]
    summary: Annotated[str, Field(description="The issue's summary.")]
    issue_type: Annotated[str | None, Field(description="Issue type name.")] = None
    status: Annotated[str | None, Field(description="Status name.")] = None
    priority: Annotated[str | None, Field(description="Priority name.")] = None
    labels: Annotated[list[str], Field(description="Labels.")] = []
    components: Annotated[list[str], Field(description="Component names.")] = []
    fix_versions: Annotated[list[str], Field(description="Fix version names.")] = []
    reporter: Annotated[str | None, Field(description="Reporter's display name.")] = None
    assignee: Annotated[str | None, Field(description="Assignee's display name.")] = None
    created: Annotated[str, Field(description="Creation time, UTC ISO-8601.")]
    updated: Annotated[str, Field(description="Last update, UTC ISO-8601.")]
    updated_at: Annotated[datetime, Field(description="Last update as an aware UTC datetime: the sync's cursor.")]
    description_html: Annotated[str, Field(description="The description as Jira renders it.")] = ""
    comments: Annotated[list[JiraComment], Field(description="Public comments, oldest first.")] = []

    @classmethod
    def from_search_hit(cls, hit: dict[str, Any], comments: list[JiraComment]) -> Self:
        fields = hit["fields"]
        return cls(
            id=str(hit["id"]),
            key=hit["key"],
            site=hit["self"].split(_REST_PATH, 1)[0],
            summary=fields.get("summary") or "",
            issue_type=cls._name(fields.get("issuetype")),
            status=cls._name(fields.get("status")),
            priority=cls._name(fields.get("priority")),
            labels=sorted(fields.get("labels") or []),
            components=sorted(cls._name(component) for component in fields.get("components") or []),
            fix_versions=sorted(cls._name(version) for version in fields.get("fixVersions") or []),
            reporter=(fields.get("reporter") or {}).get("displayName"),
            assignee=(fields.get("assignee") or {}).get("displayName"),
            created=JiraTimestamp.to_utc_iso(fields["created"]),
            updated=JiraTimestamp.to_utc_iso(fields["updated"]),
            updated_at=JiraTimestamp.to_utc(fields["updated"]),
            description_html=(hit.get("renderedFields") or {}).get("description") or "",
            comments=comments,
        )

    @staticmethod
    def project_of(issue_key: str) -> str:
        return issue_key.rsplit("-", 1)[0]

    @classmethod
    def object_key_for(cls, issue_key: str) -> str:
        """Where an issue's file lives, from the key Jira returned. The listing and the sync both name files this
        way: a project key typed in another case would otherwise list keys no file has, and every file would be
        removed."""
        return StructuredRecordFile.object_key_for(cls.project_of(issue_key), [issue_key])

    def to_record_file(self) -> StructuredRecordFile:
        return StructuredRecordFile(
            namespace=self.project_of(self.key),
            path_segments=[self.key],
            frontmatter={
                "title": self.title,
                "url": f"{self.site}/browse/{self.key}",
                "created": self.created,
                "updated": self.updated,
                "key": self.key,
                "project": self.project_of(self.key),
                "issue_type": self.issue_type,
                "status": self.status,
                "priority": self.priority,
                "labels": self.labels or None,
                "components": self.components or None,
                "fix_versions": self.fix_versions or None,
                "reporter": self.reporter,
                "assignee": self.assignee,
            },
            body=self._body(),
        )

    @property
    def title(self) -> str:
        """The key leads the title, because a citation shows the title and people refer to issues by key."""
        return f"{self.key}: {self.summary}"

    def _body(self) -> str:
        sections = [f"# {self.title}"]
        description = JiraHtml.to_markdown(self.description_html, self.site)
        if description:
            sections.append(f"## Description\n\n{description}")
        if self.comments:
            sections.append("## Comments")
            sections.extend(
                f"### {comment.author} · {comment.created_label}\n\n"
                f"{JiraHtml.to_markdown(comment.body_html, self.site)}"
                for comment in self.comments
            )
        return "\n\n".join(sections)

    @staticmethod
    def _name(value: dict[str, Any] | None) -> str | None:
        return (value or {}).get("name")
