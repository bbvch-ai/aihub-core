"""Jira Data Center through the whole adapter, on responses shaped after its REST API (``tests/data_center``).

Data Center differs from Cloud in what matters here: a personal access token, offset-free paging by id, a context
path in every link, user objects with names, wiki-rendered HTML, a 400 for invalid JQL, and internal service desk
comments marked only by a comment property that a search never returns.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_adapter import JiraAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_RECORDED = Path(__file__).with_name("data_center")
_SITE = "https://jira.acme.ch/jira"
_TOKEN = "dc-personal-access-token"


def _recorded(name: str) -> Any:
    return json.loads((_RECORDED / name).read_text())


@pytest.fixture(autouse=True)
def no_active_dlt_pipeline() -> None:
    Container()[PipelineContext].deactivate()


@pytest.fixture
def jira(monkeypatch: pytest.MonkeyPatch) -> FakeJira:
    fake = FakeJira(deployment="data_center", site=_SITE, page_size=50)
    fake.account = _recorded("myself.json")
    fake.issues["ENG"] = [_recorded("search_hit_eng_42.json")]
    fake.projects.add("ENG")
    service_desk = fake.add_issue("SD-7", summary="VPN does not connect")
    comments = _recorded("comments_sd_7.json")["comments"]
    embedded = [{k: v for k, v in c.items() if k not in ("properties", "renderedBody")} for c in comments]
    service_desk["fields"]["comment"] = {"comments": embedded, "total": 2, "maxResults": 2, "startAt": 0}
    service_desk["renderedFields"]["comment"] = {
        "comments": [{"id": c["id"], "body": c["renderedBody"]} for c in comments]
    }
    fake.paged_comments["SD-7"] = comments
    fake.project_types["SD"] = "service_desk"
    fake.install(monkeypatch)
    return fake


def _config(**changes: object) -> StructuredSyncConfig:
    options = {
        "base_url": _SITE,
        "deployment": "data_center",
        "api_token": _TOKEN,
        "project_keys": ["ENG", "SD"],
        **changes,
    }
    return StructuredSyncConfig.model_validate({"source_kind": "jira", "jira": options})


def _files(config: StructuredSyncConfig) -> dict[str, str]:
    rows = config.adapter().file_source(config.options())
    return {
        row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]: row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN]
        for row in rows
    }


def _frontmatter_and_body(markdown: str) -> tuple[dict, str]:
    _, header, body = markdown.split("---\n", 2)
    return yaml.safe_load(header), body.strip()


class TestDataCenterIssue:
    def test_the_fields_become_frontmatter_with_the_context_path_in_the_link(self, jira: FakeJira):
        frontmatter, _ = _frontmatter_and_body(_files(_config())["ENG/ENG-42.md"])

        assert frontmatter == {
            "title": "ENG-42: Login fails after a wrong password",
            "url": "https://jira.acme.ch/jira/browse/ENG-42",
            "created": "2026-10-08T07:29:58Z",
            "updated": "2026-10-08T07:34:05Z",
            "key": "ENG-42",
            "project": "ENG",
            "issue_type": "Bug",
            "status": "In Progress",
            "priority": "High",
            "labels": ["auth", "backend"],
            "components": ["API"],
            "fix_versions": ["1.0"],
            "reporter": "Khoi Nguyen",
            "assignee": "Khoi Nguyen",
        }

    def test_the_wiki_rendered_description_survives_as_markdown(self, jira: FakeJira):
        _, body = _frontmatter_and_body(_files(_config())["ENG/ENG-42.md"])

        assert "## Steps to reproduce" in body
        assert "1. Open the login page" in body
        assert "Wait for the error message" in body
        assert "| Field | Value |" in body
        assert "int attempts = 0;" in body
        assert "> Users report it since the last release." in body

    def test_links_keep_the_context_path_mentions_keep_the_name_and_images_go(self, jira: FakeJira):
        markdown = _files(_config())["ENG/ENG-42.md"]

        assert "Reported by Khoi Nguyen," in markdown
        assert '[ENG-41](https://jira.acme.ch/jira/browse/ENG-41 "Pipeline drops tables with merged cells")' in markdown
        assert "[log.txt](https://jira.acme.ch/jira/secure/attachment/10000/10000_log.txt" in markdown
        assert "ViewProfile" not in markdown
        assert "screenshot.png" not in markdown
        assert "@acme.ch" not in markdown

    def test_a_comment_restricted_to_a_role_is_left_out(self, jira: FakeJira):
        _, body = _frontmatter_and_body(_files(_config())["ENG/ENG-42.md"])

        assert "ACME-12" not in body
        assert body.count("### Khoi Nguyen · 2026-10-08") == 2
        assert "Fixed in build 1.2 — please verify." in body


class TestDataCenterServiceDesk:
    def test_an_internal_comment_marked_only_by_its_property_is_left_out(self, jira: FakeJira):
        """Data Center's search returns the internal comment like any other; only its property tells."""
        markdown = _files(_config())["SD/SD-7.md"]

        assert "Thanks, we are looking into it." in markdown
        assert "INTERNAL" not in markdown

    def test_only_service_desk_issues_cost_a_comment_request(self, jira: FakeJira):
        _files(_config())

        comment_requests = [request.url for request in jira.requests if request.url.split("?")[0].endswith("/comment")]
        assert len(comment_requests) == 1
        assert "/issue/SD-7/comment" in comment_requests[0]
        assert "expand=renderedBody%2Cproperties" in comment_requests[0]


class TestDataCenterTransport:
    def test_the_personal_access_token_is_sent_as_a_bearer_token(self, jira: FakeJira):
        _files(_config())

        assert jira.requests[0].headers["Authorization"] == f"Bearer {_TOKEN}"

    def test_the_listing_names_exactly_the_files_the_sync_writes(self, jira: FakeJira):
        config = _config()

        assert (
            config.adapter().list_record_paths(config.options())
            == set(_files(config))
            == {
                "ENG/ENG-42.md",
                "SD/SD-7.md",
            }
        )

    def test_a_rejected_token_names_the_site(self, jira: FakeJira):
        jira.fail_next(401, _recorded("unauthorized.json"))

        with pytest.raises(ValueError, match=r"Jira rejected the credentials for https://jira.acme.ch/jira \(401\)"):
            _config().adapter().dlt_source(_config().options())

    def test_an_invalid_clause_is_found_by_the_search_itself(self, jira: FakeJira):
        """Data Center has no JQL parse endpoint; its search answers an invalid query with 400."""
        jira.unknown_jql_fields = {"statuz"}

        with pytest.raises(ValueError, match="The JQL clause is invalid: Field 'statuz' does not exist"):
            _config(jql="statuz = Done").adapter().dlt_source(_config(jql="statuz = Done").options())
        assert not any("jql/parse" in request.url for request in jira.requests)

    def test_an_incremental_search_pages_by_id_within_its_window(self, monkeypatch: pytest.MonkeyPatch):
        """Data Center 11 refuses offsets past 10,000, so even the window is read a page of ids at a time."""
        fake = FakeJira(deployment="data_center", site=_SITE, page_size=1)
        fake.add_issue("ENG-1", updated="2026-10-08T09:00:00.000+0200")
        fake.add_issue("ENG-2", updated="2026-10-09T09:00:00.000+0200")
        fake.add_issue("ENG-3", updated="2026-10-10T09:00:00.000+0200")
        fake.install(monkeypatch)
        client = JiraClient(_SITE, "data_center", "", _TOKEN)

        keys = [
            hit["key"] for page in client.search(JiraAdapter._scope("ENG", "", "2026/10/09 08:55"), []) for hit in page
        ]

        assert keys == ["ENG-2", "ENG-3"]
        assert fake.sent_jql() == [
            'project = "ENG" AND updated >= "2026/10/09 08:55" ORDER BY id ASC',
            'project = "ENG" AND updated >= "2026/10/09 08:55" AND id > 10002 ORDER BY id ASC',
        ]
