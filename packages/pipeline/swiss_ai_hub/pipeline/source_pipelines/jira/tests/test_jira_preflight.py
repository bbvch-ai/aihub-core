import pytest

from swiss_ai_hub.pipeline.resources.jira.jira_client import JiraClient
from swiss_ai_hub.pipeline.resources.jira.jira_request_error import JiraRequestError
from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_adapter import JiraAdapter
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_options import JiraOptions
from swiss_ai_hub.pipeline.source_pipelines.jira.jira_preflight import JiraPreflight

_TOKEN = "s3cret-token"


def _options(**changes: object) -> JiraOptions:
    values = {
        "base_url": "https://acme.atlassian.net",
        "deployment": "cloud",
        "email": "bot@acme.test",
        "api_token": _TOKEN,
        "project_keys": ["AAA", "BBB"],
        **changes,
    }
    return JiraOptions.model_validate(values)


def _check(options: JiraOptions) -> None:
    client = JiraClient(options.base_url, options.deployment, options.email, options.api_token)
    JiraPreflight.check(client, options)


@pytest.fixture(params=["cloud", "data_center"])
def jira(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> FakeJira:
    fake = FakeJira(deployment=request.param)
    fake.add_issue("AAA-1")
    fake.projects.add("BBB")
    fake.unknown_jql_fields = {"statuz"}
    fake.install(monkeypatch)
    return fake


def _for(jira: FakeJira, **changes: object) -> JiraOptions:
    deployment = {"deployment": jira.deployment, "email": "" if jira.deployment == "data_center" else "bot@acme.test"}
    return _options(**deployment, **changes)


class TestPreflight:
    def test_a_good_configuration_passes(self, jira: FakeJira):
        _check(_for(jira, jql="issuetype != Bug"))

    def test_rejected_credentials_name_the_site_and_what_to_check(self, jira: FakeJira):
        jira.fail_next(401, {"errorMessages": ["Client must be authenticated to access this resource."]})

        with pytest.raises(ValueError, match=r"Jira rejected the credentials for https://acme.atlassian.net \(401\)"):
            _check(_for(jira))

    def test_a_locked_sign_in_is_rejected_the_same_way(self, jira: FakeJira):
        """Data Center answers 403 once a CAPTCHA locks the account after failed sign-ins."""
        jira.fail_next(403)

        with pytest.raises(ValueError, match="Jira rejected the credentials"):
            _check(_for(jira))

    def test_a_project_jira_does_not_show_names_the_project_and_the_account(self, jira: FakeJira):
        with pytest.raises(ValueError, match=r"Jira project SDD does not exist, or Seed Bot cannot see it\."):
            _check(_for(jira, project_keys=["AAA", "SDD"]))

    def test_a_renamed_project_names_its_new_key(self, jira: FakeJira):
        """Jira still answers the old key, but every issue it returns carries the new one."""
        jira.renamed_projects = {"BBB": "CCC"}

        with pytest.raises(ValueError, match=r"Jira project BBB has been renamed to CCC"):
            _check(_for(jira))

    def test_an_invalid_clause_names_jira_s_reason(self, jira: FakeJira):
        """Cloud search would answer it with no issues at all."""
        with pytest.raises(ValueError, match="The JQL clause is invalid: Field 'statuz' does not exist"):
            _check(_for(jira, jql="statuz = Done"))

    def test_no_message_carries_the_token(self, jira: FakeJira):
        jira.fail_next(401)

        with pytest.raises(ValueError) as raised:
            _check(_for(jira))

        assert _TOKEN not in str(raised.value)
        assert _TOKEN not in str(raised.value.__cause__)

    def test_any_other_failure_is_left_as_jira_s_own(self, jira: FakeJira):
        """A 400 on sign-in is no credential problem; dressing it up as one would mislead."""
        jira.fail_next(400, {"errorMessages": ["Bad request"]})

        with pytest.raises(JiraRequestError, match="400"):
            _check(_for(jira))


class TestPreflightRunsBeforeAnythingIsRead:
    def test_the_sync_and_the_listing_stop_before_any_search(self, monkeypatch: pytest.MonkeyPatch):
        fake = FakeJira()
        fake.add_issue("AAA-1")
        fake.install(monkeypatch)
        options = _options(project_keys=["AAA", "SDD"])

        with pytest.raises(ValueError, match="SDD"):
            JiraAdapter().dlt_source(options)
        with pytest.raises(ValueError, match="SDD"):
            JiraAdapter().list_record_paths(options)
        assert fake.sent_jql() == []
