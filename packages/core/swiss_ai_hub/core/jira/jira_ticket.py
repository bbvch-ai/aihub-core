from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.jira.jira_html import JiraHtml

_REST_PATH = "/rest/api/"


class JiraTicket(BaseModel):
    """One Jira ticket as an agent reads it: what a release note or a summary is written from.

    The description is markdown converted from the HTML Jira renders, the one text format Cloud and Data Center share.
    The reporter and the assignee are left out: no reader needs them, and they are people's names.
    """

    FIELDS: ClassVar[list[str]] = [
        "summary",
        "issuetype",
        "status",
        "labels",
        "components",
        "fixVersions",
        "description",
    ]

    key: Annotated[str, Field(description="Issue key, e.g. ABC-123.")]
    url: Annotated[str, Field(description="Where a person opens the ticket, from the site Jira reports itself at.")]
    project: Annotated[str, Field(description="Key of the project the ticket belongs to.")]
    issue_type: Annotated[str | None, Field(description="Issue type name, e.g. Bug or Story.")] = None
    status: Annotated[str | None, Field(description="Status name.")] = None
    summary: Annotated[str, Field(description="The ticket's summary.")]
    description: Annotated[str, Field(description="The description as markdown; empty when there is none.")] = ""
    labels: Annotated[list[str], Field(description="Labels.")] = []
    components: Annotated[list[str], Field(description="Component names.")] = []
    fix_versions: Annotated[list[str], Field(description="Fix version names.")] = []

    @classmethod
    def from_search_hit(
        cls, hit: Annotated[dict[str, Any], "One issue of a REST v2 search, with renderedFields"]
    ) -> Self:
        """The raw v2 description is wiki-markup text, never rich-text JSON; it stands in only when Jira rendered
        nothing for a description that has text."""
        fields = hit["fields"]
        site = hit["self"].split(_REST_PATH, 1)[0]
        rendered = (hit.get("renderedFields") or {}).get("description")
        raw = fields.get("description")
        return cls(
            key=hit["key"],
            url=f"{site}/browse/{hit['key']}",
            project=cls.project_of(hit["key"]),
            issue_type=cls._name(fields.get("issuetype")),
            status=cls._name(fields.get("status")),
            summary=fields.get("summary") or "",
            description=JiraHtml.to_markdown(rendered, site) or (raw if isinstance(raw, str) else ""),
            labels=sorted(fields.get("labels") or []),
            components=sorted(cls._name(component) for component in fields.get("components") or []),
            fix_versions=sorted(cls._name(version) for version in fields.get("fixVersions") or []),
        )

    @staticmethod
    def project_of(issue_key: Annotated[str, "Issue key, e.g. ABC-123"]) -> str:
        return issue_key.rsplit("-", 1)[0]

    @property
    def number(self) -> int:
        return int(self.key.rsplit("-", 1)[1])

    @staticmethod
    def _name(value: dict[str, Any] | None) -> str | None:
        return (value or {}).get("name")
