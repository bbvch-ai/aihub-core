from pathlib import Path
from types import SimpleNamespace

import pytest

from playground.jira_seed.seed_jira import (
    RELEASE_LABEL,
    SEED_LABEL,
    JiraSeeder,
    JiraSite,
    ReleaseTickets,
    SeedIssue,
    SeedScenario,
)


def _seeder(offered: dict[str, dict]) -> JiraSeeder:
    seeder = JiraSeeder(SimpleNamespace(mention="[~accountid:me]", myself={"accountId": "me"}))
    seeder._types["ENG"] = [{"id": "1", "name": "Task"}, {"id": "2", "name": "Bug"}, {"id": "3", "subtask": True}]
    for type_id in ("1", "2", "3"):
        seeder._fields[("ENG", type_id)] = offered
    return seeder


class TestScenarios:
    def test_every_case_is_named_once_and_every_parent_exists(self):
        cases = [issue.case for issue in SeedScenario.load().issues]

        assert len(cases) == len(set(cases))
        assert {issue.parent_case for issue in SeedScenario.load().issues} - {None} <= set(cases)

    def test_a_sub_task_is_created_after_its_parent(self):
        order = [issue.case for issue in SeedScenario.load().selected(None)]

        assert order.index("subtask") > order.index("metadata")

    def test_an_unknown_case_is_refused(self):
        with pytest.raises(RuntimeError, match="Unknown case"):
            SeedScenario.load().selected({"no-such-case"})

    def test_the_blocks_of_a_description_are_kept_apart(self):
        """A wiki list runs on until a blank line, so without one Jira renders the heading after it inside the list."""
        rich = next(issue for issue in SeedScenario.load().issues if issue.case == "rich-formatting")

        assert "# Press _Sign in_ again\n\nh3. Environment" in rich.text(mention="[~me]")
        assert "|Tenant|acme|\n\n{code:java}" in rich.text(mention="[~me]")


class TestFields:
    def test_fields_the_create_screen_lacks_are_skipped(self, capsys: pytest.CaptureFixture[str]):
        issue = SeedIssue(case="x", summary="S", components=["API"], priority="High", expect="-")
        offered = {"summary": {}, "labels": {}, "priority": {"allowedValues": [{"name": "High"}]}}

        fields = _seeder(offered).fields_for("ENG", issue, existing={"API"}, parent_key=None)

        assert fields["priority"] == {"name": "High"}
        assert fields["labels"] == [SEED_LABEL, "aihub-case-x"]
        assert "components" not in fields
        assert "'components' is not on the create screen of ENG" in capsys.readouterr().out

    def test_a_priority_the_scheme_lacks_is_skipped(self):
        issue = SeedIssue(case="x", summary="S", priority="High", expect="-")
        offered = {"priority": {"allowedValues": [{"name": "Major"}, {"name": "Minor"}]}}

        assert "priority" not in _seeder(offered).fields_for("ENG", issue, existing=set(), parent_key=None)

    def test_a_sub_task_names_its_parent_and_the_mention_is_filled_in(self):
        issue = SeedIssue(case="x", type="subtask", summary="S", description="For {me}", expect="-")

        fields = _seeder({"parent": {}, "description": {}}).fields_for("ENG", issue, set(), parent_key="ENG-7")

        assert fields["issuetype"] == {"id": "3"}
        assert fields["parent"] == {"key": "ENG-7"}
        assert fields["description"] == "For [~accountid:me]"


class TestServiceManagementSpace:
    def test_a_space_without_bugs_uses_its_first_standard_type(self, capsys: pytest.CaptureFixture[str]):
        seeder = _seeder({})
        seeder._types["SD"] = [{"id": "9", "name": "Service request"}, {"id": "8", "name": "Incident"}]

        assert seeder._issue_type("SD", "bug")["name"] == "Incident"
        assert seeder._issue_type("SD", "story")["name"] == "Service request"
        assert "SD has no Story / Task" in capsys.readouterr().out

    def test_a_case_needing_a_missing_sub_task_type_is_skipped(self, capsys: pytest.CaptureFixture[str]):
        seeder = _seeder({})
        seeder._types["SD"] = [{"id": "9", "name": "Task"}]
        issue = SeedIssue(case="subtask", type="subtask", summary="S", parent_case="metadata", expect="-")

        assert seeder._create("SD", issue, existing=set(), created={}) is None
        assert "SD has no sub-task issue type" in capsys.readouterr().out

    def test_an_internal_comment_is_only_written_in_a_service_management_space(self):
        site = SimpleNamespace(mention="", myself={}, calls=[])
        site.call = lambda method, path, **kwargs: site.calls.append((path, kwargs.get("json")))
        seeder = JiraSeeder(site)
        issue = SeedIssue(
            case="x", summary="S", expect="-", comments=[{"body": "public"}, {"body": "agents only", "internal": True}]
        )
        seeder._project_types.update({"ENG": "software", "SD": "service_desk"})

        seeder._add_comments("ENG", "ENG-1", issue)
        seeder._add_comments("SD", "SD-1", issue)

        assert [body["body"] for path, body in site.calls if path.startswith("/rest/api/2/issue/ENG-1")] == ["public"]
        [internal] = [
            body for path, body in site.calls if path.startswith("/rest/api/2/issue/SD-1") and "properties" in body
        ]
        assert internal["properties"] == [{"key": "sd.public.comment", "value": {"internal": True}}]


class _RecordingSite(JiraSite):
    """A Cloud site answering from a table instead of the network."""

    def __init__(self, answers: dict[str, object], groups: list[str]):
        self.deployment = "cloud"
        self.me = {"accountId": "me-1", "displayName": "Me"}
        self.answers = answers
        self.groups = groups
        self.calls: list[tuple[str, str, object]] = []

    def call(self, method: str, path: str, **kwargs: object) -> object:
        self.calls.append((method, path, kwargs.get("json")))
        return self.answers.get(path, {"key": "ENG-9"})

    def my_groups(self) -> list[str]:
        return self.groups


def _roles(administrators: list[dict], members: list[dict]) -> dict[str, object]:
    base = "https://acme.atlassian.net/rest/api/2/project/10000/role"
    return {
        "/rest/api/2/project/ENG/role": {"Administrators": f"{base}/1", "Member": f"{base}/2"},
        "/rest/api/2/project/ENG/role/1": {"actors": administrators},
        "/rest/api/2/project/ENG/role/2": {"actors": members},
    }


class TestOnlyTheSeedingAccount:
    def test_a_comment_is_restricted_to_a_role_the_account_is_in(self):
        """Jira refuses a role the author is not in ("You are currently not a member of the project role")."""
        me = {"type": "atlassian-user-role-actor", "actorUser": {"accountId": "me-1"}}
        other = {"type": "atlassian-user-role-actor", "actorUser": {"accountId": "someone-else"}}

        site = _RecordingSite(_roles(administrators=[other], members=[me]), groups=[])

        assert JiraSeeder(site)._restriction("ENG") == {"type": "role", "value": "Member"}

    def test_a_role_held_through_a_group_counts(self):
        group = {"type": "atlassian-group-role-actor", "actorGroup": {"name": "site-admins"}}

        site = _RecordingSite(_roles(administrators=[group], members=[]), groups=["site-admins"])

        assert JiraSeeder(site)._restriction("ENG") == {"type": "role", "value": "Administrators"}

    def test_without_a_role_a_group_of_the_account_restricts_the_comment(self):
        site = _RecordingSite(_roles(administrators=[], members=[]), groups=["jira-software-users"])

        assert JiraSeeder(site)._restriction("ENG") == {"type": "group", "value": "jira-software-users"}

    def test_every_issue_is_assigned_to_the_seeding_account(self):
        fields = _seeder({"assignee": {}}).fields_for("ENG", SeedIssue(case="x", summary="S", expect="-"), set(), None)

        assert fields["assignee"] == {"accountId": "me"}

    def test_an_issue_whose_create_screen_lacks_the_assignee_is_assigned_right_after(self):
        site = _RecordingSite({}, groups=[])
        seeder = JiraSeeder(site)
        seeder._types["ENG"] = [{"id": "1", "name": "Task"}]
        seeder._fields[("ENG", "1")] = {"summary": {}}

        seeder._create("ENG", SeedIssue(case="x", summary="S", expect="-"), existing=set(), created={})

        assert ("PUT", "/rest/api/2/issue/ENG-9/assignee", {"accountId": "me-1"}) in site.calls


class TestRestrictedComments:
    def test_a_site_without_group_restrictions_skips_the_restricted_comment(self, capsys: pytest.CaptureFixture[str]):
        site = _RecordingSite(_roles(administrators=[], members=[]), groups=["jira-users"])
        refused = RuntimeError('400: {"errorMessages":["GROUP_VISIBILITY_SETTING_NOT_ENABLED"]}')
        posted: list[dict] = []

        def call(method: str, path: str, **kwargs: object) -> object:
            if path.endswith("/comment"):
                if "visibility" in kwargs["json"]:
                    raise refused
                posted.append(kwargs["json"])
                return {}
            return site.answers.get(path, {})

        site.call = call
        issue = SeedIssue(
            case="restricted-comment",
            summary="S",
            expect="-",
            comments=[{"body": "a", "restricted": True}, {"body": "b", "restricted": True}, {"body": "c"}],
        )

        JiraSeeder(site)._add_comments("ENG", "ENG-1", issue)

        assert [comment["body"] for comment in posted] == ["c"]
        assert "Add yourself to a role of ENG" in capsys.readouterr().out


class TestResume:
    def test_cases_already_in_the_project_are_not_created_again(self, capsys: pytest.CaptureFixture[str]):
        site = _RecordingSite({"/rest/api/2/project/ENG/components": [], "/rest/api/2/project/ENG/versions": []}, [])
        site.search = lambda jql, fields: [{"key": "ENG-8", "fields": {"labels": [SEED_LABEL, "aihub-case-plain"]}}]

        seeded = JiraSeeder(site).seed("ENG", [SeedIssue(case="plain", summary="S", expect="-")])

        assert [key for _, key in seeded] == ["ENG-8"]
        assert not [path for method, path, _ in site.calls if method == "POST"]
        assert "ENG-8      plain (already there" in capsys.readouterr().out


class TestClean:
    def test_an_issue_someone_else_holds_is_taken_over_before_it_is_deleted(self):
        """Jira tells the assignee about a deletion; the colleague must not hear of the seed data at all."""
        hits = [
            {"key": "ENG-4", "fields": {"issuetype": {}, "assignee": {"accountId": "colleague"}}},
            {"key": "ENG-5", "fields": {"issuetype": {}, "assignee": {"accountId": "me-1"}}},
        ]
        site = _RecordingSite({}, groups=[])
        site.search = lambda jql, fields: hits

        JiraSeeder(site).clean("ENG")

        assert [(method, path) for method, path, _ in site.calls] == [
            ("PUT", "/rest/api/2/issue/ENG-4/assignee"),
            ("DELETE", "/rest/api/2/issue/ENG-4"),
            ("DELETE", "/rest/api/2/issue/ENG-5"),
        ]


class TestSite:
    def test_the_env_file_is_read_without_quotes_or_export(self, tmp_path: Path):
        env = tmp_path / "cloud.env"
        env.write_text("# comment\nexport JIRA_URL='https://acme.atlassian.net'\nJIRA_TOKEN=\"t=1\"\n")

        assert JiraSite._read_env_file(env) == {"JIRA_URL": "https://acme.atlassian.net", "JIRA_TOKEN": "t=1"}


class TestRelease:
    def test_tickets_rotate_over_the_kinds_and_name_an_area(self):
        tickets = ReleaseTickets.load()

        kinds = [tickets.ticket(number, ["bug", "story"])[0] for number in range(4)]

        assert kinds == ["bug", "story", "bug", "story"]
        assert tickets.ticket(0, ["bug"])[1] == "Login page shows an error after the session expires"

    def test_the_first_dozens_of_tickets_of_a_kind_read_differently(self):
        tickets = ReleaseTickets.load()

        summaries = [tickets.ticket(number, ["bug"])[1] for number in range(24)]

        assert len(set(summaries)) == 24

    def test_wiki_monospace_survives_the_area_being_filled_in(self):
        tickets = ReleaseTickets.load()
        number = next(n for n in range(200) if "Keyboard shortcuts" in tickets.ticket(n, ["story"])[1])

        assert "{{g}}" in tickets.ticket(number, ["story"])[2]

    def test_an_unknown_kind_is_refused(self):
        with pytest.raises(RuntimeError, match="Unknown release ticket kind"):
            ReleaseTickets.load().ticket(0, ["epic"])

    def test_a_ticket_carries_the_fix_version_and_the_release_label(self):
        fields = _seeder({}).release_fields("ENG", "2.0", ("bug", "Fix it", "Text"))

        assert fields["fixVersions"] == [{"name": "2.0"}]
        assert fields["labels"] == [SEED_LABEL, RELEASE_LABEL]
        assert fields["issuetype"] == {"id": "2"}

    def test_a_release_is_created_in_batches_and_every_ticket_assigned_to_the_seeding_account(self):
        site = _RecordingSite(
            {
                "/rest/api/2/project/ENG/versions": [{"name": "2.0"}],
                "/rest/api/2/issue/bulk": {"issues": [{"key": "ENG-9"}]},
            },
            groups=[],
        )
        site.search = lambda jql, fields="summary": []
        seeder = JiraSeeder(site)
        seeder._types["ENG"] = [{"id": "1", "name": "Task"}, {"id": "2", "name": "Bug"}]

        seeder.release("ENG", "2.0", 120, ["bug", "task"], ReleaseTickets.load())

        bulk = [body for method, path, body in site.calls if path == "/rest/api/2/issue/bulk"]
        assert [len(body["issueUpdates"]) for body in bulk] == [50, 50, 20]
        assert ("PUT", "/rest/api/2/issue/ENG-9/assignee", {"accountId": "me-1"}) in site.calls

    def test_a_release_already_there_is_not_created_again(self, capsys: pytest.CaptureFixture[str]):
        site = _RecordingSite({"/rest/api/2/project/ENG/versions": [{"name": "2.0"}]}, groups=[])
        site.search = lambda jql, fields="summary": [{"key": "ENG-40"}]

        JiraSeeder(site).release("ENG", "2.0", 120, ["bug"], ReleaseTickets.load())

        assert not [path for _, path, _ in site.calls if path == "/rest/api/2/issue/bulk"]
        assert "release 2.0: 1 tickets already there" in capsys.readouterr().out
