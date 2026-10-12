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
