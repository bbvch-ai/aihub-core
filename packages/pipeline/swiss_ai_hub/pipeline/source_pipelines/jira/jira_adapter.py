from collections.abc import Iterator
from typing import Any

import dlt
from dlt.extract import DltResource, DltSource
from swiss_ai_hub.core.form import ChipsInput, InputText, Password, Select, Textarea
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_comment import JiraComment
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_issue import JiraIssue
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_options import JiraOptions
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

_I18N = "lib.source_pipelines.structured.config.jira"
_DEPLOYMENT_REF = "jira_deployment"
_ISSUE_FIELDS = [
    "summary",
    "issuetype",
    "status",
    "priority",
    "labels",
    "components",
    "fixVersions",
    "reporter",
    "assignee",
    "created",
    "updated",
    "description",
    "comment",
]
# The listing needs only each issue's key, which every hit carries; one small field keeps the pages light.
_LISTING_FIELDS = ["summary"]


class JiraAdapter(AbstractStructuredSourceAdapter[JiraOptions]):
    """Syncs the issues of the configured Jira projects, one markdown file per issue at ``{project}/{key}.md``.

    Each project becomes a namespace. A file holds the issue's fields as frontmatter and its description and public
    comments as text. Projects are searched one at a time, so an issue a JQL clause would pull in from another
    project is refused instead of creating a namespace nobody configured.
    """

    kind = "jira"
    display_name = LocaleString.from_i18n_path(f"{_I18N}.display_name")

    @classmethod
    def options_form(cls) -> JiraOptions:
        shown = cls.shown_for(cls.kind)
        return JiraOptions(
            base_url=InputText(
                **cls._labels("base_url"),
                placeholder="https://acme.atlassian.net",
                required=True,
                additional_validation_rules="url",
                condition_if=shown,
            ),
            deployment=Select(
                **cls._labels("deployment"),
                options=[
                    {"label": LocaleString.from_i18n_path(f"{_I18N}.deployment.{value}"), "value": value}
                    for value in ("cloud", "data_center")
                ],
                option_label="label",
                option_value="value",
                ref=_DEPLOYMENT_REF,
                required=True,
                condition_if=shown,
            ),
            email=InputText(
                **cls._labels("email"),
                required=True,
                condition_if=f"{shown} && $get({_DEPLOYMENT_REF}).value === 'cloud'",
            ),
            api_token=Password(
                **cls._labels("api_token"), feedback=False, toggle_mask=True, required=True, condition_if=shown
            ),
            project_keys=ChipsInput(
                **cls._labels("project_keys"), placeholder="ABC", required=True, condition_if=shown
            ),
            jql=Textarea(**cls._labels("jql"), placeholder='issuetype != "Service Request"', condition_if=shown),
        )

    def dlt_source(self, options: JiraOptions) -> DltSource:
        self._refuse_unusable(options)
        client = self._client(options)

        @dlt.source(name="jira")
        def jira() -> DltResource:
            @dlt.resource(name="issues", primary_key="id")
            def issues() -> Iterator[list[dict[str, Any]]]:
                for project in options.projects():
                    for page in client.search(self._scope(project, options.jql), _ISSUE_FIELDS, rendered=True):
                        yield [self._issue(client, project, hit).model_dump() for hit in page]

            return issues

        return jira()

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile:
        return JiraIssue.model_validate(record).to_record_file()

    def list_record_paths(self, options: JiraOptions) -> set[str]:
        self._refuse_unusable(options)
        client = self._client(options)
        return {
            JiraIssue.object_key_for(self._own_key(project, hit))
            for project in options.projects()
            for page in client.search(self._scope(project, options.jql), _LISTING_FIELDS)
            for hit in page
        }

    def _issue(self, client: JiraClient, project: str, hit: dict[str, Any]) -> JiraIssue:
        key = self._own_key(project, hit)
        if JiraComment.has_more_than_embedded(hit):
            comments = JiraComment.from_paged(client.comments(key))
        else:
            comments = JiraComment.from_embedded(hit)
        return JiraIssue.from_search_hit(hit, comments)

    @staticmethod
    def _own_key(project: str, hit: dict[str, Any]) -> str:
        """A clause such as ``a OR b`` still matches inside its parentheses, but a crafted one could reach past them;
        an issue of an unconfigured project would land in a namespace nobody asked for."""
        key = hit["key"]
        if JiraIssue.project_of(key) != project:
            raise ValueError(f"Jira returned {key} while searching project {project}; check the JQL clause.")
        return key

    @staticmethod
    def _scope(project: str, jql: str) -> str:
        """The clause is parenthesised, so an ``OR`` in it cannot widen the search beyond the project."""
        scope = f'project = "{project}"'
        return f"{scope} AND ({jql.strip()})" if jql.strip() else scope

    @staticmethod
    def _client(options: JiraOptions) -> JiraClient:
        return JiraClient(
            base_url=options.base_url, deployment=options.deployment, email=options.email, token=options.api_token
        )

    @staticmethod
    def _refuse_unusable(options: JiraOptions) -> None:
        problems = options.problems()
        if problems:
            raise ValueError(f"The Jira source cannot sync: {'; '.join(problems)}.")

    @staticmethod
    def _labels(field: str) -> dict[str, LocaleString]:
        return {
            "label": LocaleString.from_i18n_path(f"{_I18N}.{field}.label"),
            "help": LocaleString.from_i18n_path(f"{_I18N}.{field}.help"),
        }
