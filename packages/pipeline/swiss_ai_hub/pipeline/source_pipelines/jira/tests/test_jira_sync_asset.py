"""Real syncs of the shipped structured asset against a fake Jira: dlt normalises and loads Jira's nested records."""

from unittest.mock import MagicMock

import pytest
from dagster import AssetKey

from swiss_ai_hub.pipeline.assets.factories.structured_to_data_lake.structured_sync_factory import (
    structured_sync_factory,
)
from swiss_ai_hub.pipeline.ops.structured.tests.test_structured_sync_asset import World
from swiss_ai_hub.pipeline.resources.jira.tests.fake_jira import FakeJira
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_ASSET = structured_sync_factory(
    AssetKey(["structured_source_to_datalake", "records"]), source="structured", config_type=StructuredSyncConfig
)


@pytest.fixture
def jira(world: World, monkeypatch: pytest.MonkeyPatch) -> FakeJira:
    fake = FakeJira(page_size=2)
    fake.add_issue("AAA-1", comments=2, labels=["backend"])
    fake.add_issue("AAA-2", assignee={"displayName": "Ada"})
    fake.add_issue("BBB-1", comments=1)
    fake.install(monkeypatch)
    world.configs["jira-db"] = StructuredSyncConfig.model_validate(
        {
            "source_kind": "jira",
            "jira": {
                "base_url": "https://acme.atlassian.net",
                "email": "bot@acme.test",
                "api_token": "s3cret-token",
                "project_keys": ["AAA", "BBB"],
            },
        }
    )
    world.rows["jira-db"] = MagicMock(source="structured", deleting=False)
    return fake


class TestJiraSync:
    def test_a_first_sync_writes_one_file_per_issue_in_its_project_namespace(self, world: World, jira: FakeJira):
        result = world.sync("jira-db", asset=_ASSET)

        assert result.success
        assert world.files("jira-db") == ["AAA/AAA-1.md", "AAA/AAA-2.md", "BBB/BBB-1.md"]
        assert "### Commenter 2" in world.body("jira-db", "AAA/AAA-1.md")
        assert "labels:\n- backend\n" in world.body("jira-db", "AAA/AAA-1.md")

    def test_a_second_sync_of_unchanged_issues_writes_nothing(self, world: World, jira: FakeJira):
        world.sync("jira-db", asset=_ASSET)
        writes = world.file_writes()

        result = world.sync("jira-db", asset=_ASSET)

        assert result.success
        assert world.file_writes() == writes
        assert world.step_metadata(result, "sync_structured_records")["Files written"] == 0

    def test_an_issue_deleted_in_jira_is_removed(self, world: World, jira: FakeJira):
        world.sync("jira-db", asset=_ASSET)
        jira.issues["AAA"] = [hit for hit in jira.issues["AAA"] if hit["key"] != "AAA-2"]

        assert world.sync("jira-db", asset=_ASSET).success

        assert world.files("jira-db") == ["AAA/AAA-1.md", "BBB/BBB-1.md"]
        assert world.announced(world.removed_events) == ["AAA/AAA-2.md"]

    def test_an_edited_issue_is_rewritten(self, world: World, jira: FakeJira):
        world.sync("jira-db", asset=_ASSET)
        jira.issues["BBB"][0]["fields"]["summary"] = "Renamed"

        assert world.sync("jira-db", asset=_ASSET).success

        assert "title: 'BBB-1: Renamed'" in world.body("jira-db", "BBB/BBB-1.md")

    @pytest.mark.parametrize(
        ("change", "message"),
        [
            ({"project_keys": ["AAA", "BBB", "SDD"]}, "Jira project SDD does not exist, or Seed Bot cannot see it."),
            ({"jql": "statuz = Done"}, "The JQL clause is invalid: Field 'statuz' does not exist"),
        ],
    )
    def test_a_project_or_clause_jira_would_answer_with_nothing_fails_and_removes_nothing(
        self, world: World, jira: FakeJira, change: dict, message: str
    ):
        """Jira answers both with no issues; the listing would then remove every file of the affected projects."""
        world.sync("jira-db", asset=_ASSET)
        jira.unknown_jql_fields = {"statuz"}
        options = world.configs["jira-db"].jira.model_dump()
        world.configs["jira-db"] = StructuredSyncConfig.model_validate(
            {"source_kind": "jira", "jira": {**options, **change}}
        )

        result = world.sync("jira-db", asset=_ASSET)

        assert not result.success
        [failure] = result.get_step_failure_events()
        assert message in failure.event_specific_data.error.to_string()
        assert world.files("jira-db") == ["AAA/AAA-1.md", "AAA/AAA-2.md", "BBB/BBB-1.md"]

    def test_rejected_credentials_fail_the_sync_and_remove_nothing(self, world: World, jira: FakeJira):
        world.sync("jira-db", asset=_ASSET)
        jira.fail_next(401, {"errorMessages": ["Client must be authenticated to access this resource."]})

        result = world.sync("jira-db", asset=_ASSET)

        assert not result.success
        [failure] = result.get_step_failure_events()
        shown_on_the_run_page = failure.event_specific_data.error.to_string()
        assert "ValueError: Jira rejected the credentials for https://acme.atlassian.net (401)" in shown_on_the_run_page
        assert "s3cret-token" not in shown_on_the_run_page
        assert world.files("jira-db") == ["AAA/AAA-1.md", "AAA/AAA-2.md", "BBB/BBB-1.md"]


def _updated(day: int) -> str:
    return f"2026-10-{day:02d}T10:00:00.000+0200"


@pytest.fixture
def dated_jira(world: World, monkeypatch: pytest.MonkeyPatch) -> FakeJira:
    """Issues last updated on different days, so a window that starts after a day leaves that issue out."""
    fake = FakeJira(page_size=2)
    fake.add_issue("AAA-1", updated=_updated(1))
    fake.add_issue("AAA-2", updated=_updated(2))
    fake.add_issue("BBB-1", updated=_updated(3))
    fake.install(monkeypatch)
    world.configs["jira-db"] = StructuredSyncConfig.model_validate(
        {
            "source_kind": "jira",
            "jira": {
                "base_url": "https://acme.atlassian.net",
                "email": "bot@acme.test",
                "api_token": "s3cret-token",
                "project_keys": ["AAA", "BBB"],
            },
        }
    )
    world.rows["jira-db"] = MagicMock(source="structured", deleting=False)
    return fake


def _issue_searches(jira: FakeJira) -> list[str]:
    return [jql for jql in jira.sent_jql() if "updated >=" in jql]


class TestIncrementalSync:
    def test_the_first_sync_reads_everything(self, world: World, dated_jira: FakeJira):
        world.sync("jira-db", asset=_ASSET)

        assert _issue_searches(dated_jira) == []
        assert world.files("jira-db") == ["AAA/AAA-1.md", "AAA/AAA-2.md", "BBB/BBB-1.md"]

    def test_the_next_sync_asks_only_for_what_changed_since_the_cursor_less_five_minutes(
        self, world: World, dated_jira: FakeJira
    ):
        """The cursor is BBB-1's 08:00 UTC on day 3, kept in S3 between runs; five minutes earlier is 09:55 in
        Zurich. Every project is asked from that same minute."""
        world.sync("jira-db", asset=_ASSET)
        dated_jira.requests.clear()

        result = world.sync("jira-db", asset=_ASSET)

        assert result.success
        assert world.step_metadata(result, "sync_structured_records")["Resumed from stored state"] is True
        assert _issue_searches(dated_jira) == [
            'project = "AAA" AND updated >= "2026/10/03 09:55" ORDER BY id ASC',
            'project = "BBB" AND updated >= "2026/10/03 09:55" ORDER BY id ASC',
        ]

    def test_an_edited_issue_is_fetched_and_rewritten_and_the_others_are_not_fetched(
        self, world: World, dated_jira: FakeJira
    ):
        world.sync("jira-db", asset=_ASSET)
        aaa_1 = dated_jira.issues["AAA"][0]
        aaa_1["fields"].update(summary="Edited in Jira", updated=_updated(5))

        result = world.sync("jira-db", asset=_ASSET)

        sync = world.step_metadata(result, "sync_structured_records")
        assert (sync["Rows loaded"], sync["Files written"]) == (2, 1), "AAA-1 changed; BBB-1 is inside the overlap"
        assert "title: 'AAA-1: Edited in Jira'" in world.body("jira-db", "AAA/AAA-1.md")
        assert world.files("jira-db") == ["AAA/AAA-1.md", "AAA/AAA-2.md", "BBB/BBB-1.md"]

    def test_deletions_are_still_found_by_the_full_listing(self, world: World, dated_jira: FakeJira):
        """The incremental fetch never sees a deleted issue; the listing, which ignores the cursor, does."""
        world.sync("jira-db", asset=_ASSET)
        dated_jira.issues["AAA"] = [hit for hit in dated_jira.issues["AAA"] if hit["key"] != "AAA-1"]

        assert world.sync("jira-db", asset=_ASSET).success

        assert world.files("jira-db") == ["AAA/AAA-2.md", "BBB/BBB-1.md"]

    def test_a_new_project_reads_everything_again(self, world: World, dated_jira: FakeJira):
        """An old cursor would skip the new project's older issues; a changed scope starts from no cursor."""
        world.sync("jira-db", asset=_ASSET)
        dated_jira.add_issue("CCC-1", updated=_updated(1))
        options = world.configs["jira-db"].jira.model_dump()
        world.configs["jira-db"] = StructuredSyncConfig.model_validate(
            {"source_kind": "jira", "jira": {**options, "project_keys": ["AAA", "BBB", "CCC"]}}
        )
        dated_jira.requests.clear()

        result = world.sync("jira-db", asset=_ASSET)

        assert _issue_searches(dated_jira) == []
        assert world.step_metadata(result, "sync_structured_records")["Resumed from stored state"] is False
        assert "CCC/CCC-1.md" in world.files("jira-db")
