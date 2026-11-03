import pytest
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext
from dlt.extract.exceptions import ResourceExtractionError
from pydantic import ValidationError
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater

from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_adapter import JiraAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_TOKEN = "s3cret-token"


@pytest.fixture(autouse=True)
def no_active_dlt_pipeline() -> None:
    """Outside a pipeline, dlt resolves state from whichever pipeline last ran in this process."""
    Container()[PipelineContext].deactivate()


@pytest.fixture
def jira(monkeypatch: pytest.MonkeyPatch) -> FakeJira:
    fake = FakeJira(page_size=2)
    for number in range(1, 4):
        fake.add_issue(f"AAA-{number}", comments=1)
    fake.add_issue("BBB-1")
    fake.install(monkeypatch)
    return fake


def _config(**jira: object) -> StructuredSyncConfig:
    options = {
        "base_url": "https://acme.atlassian.net",
        "deployment": "cloud",
        "email": "bot@acme.test",
        "api_token": _TOKEN,
        "project_keys": ["AAA", "BBB"],
        **jira,
    }
    return StructuredSyncConfig.model_validate({"source_kind": "jira", "jira": options})


def _files(config: StructuredSyncConfig) -> dict[str, str]:
    rows = config.adapter().file_source(config.options())
    return {
        row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]: row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN]
        for row in rows
    }


class TestSync:
    def test_every_issue_of_every_project_becomes_a_file_in_its_namespace(self, jira: FakeJira):
        files = _files(_config())

        assert set(files) == {"AAA/AAA-1.md", "AAA/AAA-2.md", "AAA/AAA-3.md", "BBB/BBB-1.md"}
        assert "## Comments" in files["AAA/AAA-1.md"]
        assert "title: 'AAA-1: Summary of AAA-1'" in files["AAA/AAA-1.md"]

    def test_the_listing_names_exactly_the_files_the_sync_writes(self, jira: FakeJira):
        """A listed key without its file, or a file never listed, would make the reconcile step delete data."""
        config = _config()

        assert config.adapter().list_record_paths(config.options()) == set(_files(config))

    def test_lower_case_project_keys_name_the_same_files(self, jira: FakeJira):
        config = _config(project_keys=["aaa", " bbb "])

        assert config.adapter().list_record_paths(config.options()) == set(_files(_config()))

    def test_comments_beyond_the_twenty_a_search_embeds_are_read_from_the_issue(self, monkeypatch: pytest.MonkeyPatch):
        fake = FakeJira(page_size=50)
        fake.add_issue("AAA-1", comments=23)
        fake.install(monkeypatch)

        files = _files(_config(project_keys=["AAA"]))

        assert files["AAA/AAA-1.md"].count("### Commenter") == 23
        assert any("/issue/AAA-1/comment" in request.url for request in fake.requests)

    def test_the_jql_clause_narrows_each_project_and_cannot_widen_it(self, jira: FakeJira):
        _files(_config(jql="issuetype = Bug OR issuetype = Story"))

        assert set(jira.sent_jql()) == {
            'project = "AAA" AND (issuetype = Bug OR issuetype = Story) ORDER BY id ASC',
            'project = "BBB" AND (issuetype = Bug OR issuetype = Story) ORDER BY id ASC',
        }

    def test_an_issue_of_another_project_is_refused(self, monkeypatch: pytest.MonkeyPatch):
        """A crafted clause could reach past its parentheses; its issues must not create namespaces."""
        fake = FakeJira()
        fake.add_issue("AAA-1")
        fake.issues["AAA"][0]["key"] = "ZZZ-9"
        fake.install(monkeypatch)

        config = _config(project_keys=["AAA"])

        with pytest.raises(ResourceExtractionError, match="Jira returned ZZZ-9 while searching project AAA"):
            _files(config)

    def test_data_center_is_read_the_same_way(self, monkeypatch: pytest.MonkeyPatch):
        fake = FakeJira(deployment="data_center", site="https://jira.acme.ch/jira")
        fake.add_issue("AAA-1")
        fake.add_issue("AAA-2")
        fake.add_issue("AAA-3")
        fake.install(monkeypatch)
        config = _config(base_url="https://jira.acme.ch/jira", deployment="data_center", email="", project_keys=["AAA"])

        files = _files(config)

        assert (
            set(files)
            == config.adapter().list_record_paths(config.options())
            == {
                "AAA/AAA-1.md",
                "AAA/AAA-2.md",
                "AAA/AAA-3.md",
            }
        )
        assert "url: https://jira.acme.ch/jira/browse/AAA-1" in files["AAA/AAA-1.md"]


class TestUnusableConfiguration:
    @pytest.mark.parametrize(
        ("options", "reason"),
        [
            ({"project_keys": None}, "no project key is given"),
            ({"project_keys": ["AAA", "1AB"]}, "1AB is not a Jira project key"),
            ({"email": ""}, "Jira Cloud needs the e-mail"),
            ({"api_token": ""}, "the token is missing"),
            ({"base_url": ""}, "the Jira URL is missing"),
            ({"jql": "status = Done order  by created"}, "must not contain ORDER BY"),
        ],
    )
    def test_the_sync_fails_naming_what_to_fix(self, jira: FakeJira, options: dict, reason: str):
        config = _config(**options)
        adapter, source_options = config.adapter(), config.options()

        with pytest.raises(ValueError, match=reason):
            adapter.dlt_source(source_options)
        with pytest.raises(ValueError, match=reason):
            adapter.list_record_paths(source_options)
        assert jira.requests == []

    def test_data_center_needs_no_email(self, jira: FakeJira):
        assert _config(deployment="data_center", email="").options().problems() == []

    @pytest.mark.parametrize(
        "base_url",
        [
            "ftp://jira.acme.ch",
            "https://bot:token@acme.atlassian.net",
            "jira.acme.ch",
            "http://seaweedfs-filer:8888/buckets/other/x.md?",
            "https://jira.acme.ch/jira#",
            "https://jira.acme.ch/jira?os_authType=basic",
        ],
    )
    def test_a_url_that_is_not_plain_http_is_refused_when_saved(self, base_url: str):
        """The constraint sits in the type, so the API's schema validation refuses it before anything is stored. A
        query or fragment would turn the API path appended to the URL into a query, so it could name any path."""
        with pytest.raises(ValidationError):
            _config(base_url=base_url)

    def test_an_unknown_deployment_is_refused_when_saved(self):
        with pytest.raises(ValidationError):
            _config(deployment="server")

    def test_the_announced_schema_carries_both_constraints(self):
        schema = str(ConfigSpecs.from_form(StructuredSyncConfig.as_form(), "StructuredSyncConfig").config_schema)

        assert "https?://" in schema
        assert "data_center" in schema


class TestForm:
    def test_the_token_is_the_one_secret(self):
        assert {path for path in StructuredSyncConfig.secret_field_paths() if path.startswith("jira.")} == {
            "jira.api_token"
        }

    def test_the_email_is_asked_only_for_jira_cloud(self):
        [group] = [element for element in StructuredSyncConfig.as_form().to_formkit_form() if element.name == "jira"]
        email = next(child for child in group.children if child.name == "email")

        assert email.condition_if == (
            "$get(structured_source_kind).value === 'jira' && $get(jira_deployment).value === 'cloud'"
        )

    def test_rotating_the_token_keeps_the_cursor_and_retyping_projects_does_not_reset_it(self):
        assert _config(api_token="a").scope_fingerprint() == _config(api_token="b").scope_fingerprint()
        assert _config(project_keys=["BBB", "AAA"]).scope_fingerprint() == _config().scope_fingerprint()
        assert _config(project_keys=["AAA"]).scope_fingerprint() != _config().scope_fingerprint()

    def test_the_kind_is_offered_by_its_name(self):
        assert JiraAdapter.display_name.en == "Jira"
