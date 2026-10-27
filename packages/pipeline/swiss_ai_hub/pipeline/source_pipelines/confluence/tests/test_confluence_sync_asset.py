"""Real syncs of the shipped structured asset against a fake Confluence, run after run, as the daily schedule does."""

import re
from unittest.mock import MagicMock

import pytest
from dagster import AssetKey
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.assets.factories.structured_to_data_lake.structured_sync_factory import (
    structured_sync_factory,
)
from swiss_ai_hub.pipeline.ops.structured.tests.test_structured_sync_asset import World
from swiss_ai_hub.pipeline.resources.confluence.tests.fake_confluence import SITES, FakeConfluence
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig

_ASSET = structured_sync_factory(
    AssetKey(["structured_source_to_datalake", "records"]), source="structured", config_type=StructuredSyncConfig
)
_TREE = [
    "ENG/Engineering.md",
    "ENG/Engineering/Runbooks.md",
    "ENG/Engineering/Runbooks/Deploy.md",
    "ENG/Engineering/Runbooks/Rollback.md",
    "OPS/Operations.md",
]
_ID_LIST = re.compile(r"^id in \((.*)\)$")


@pytest.fixture(autouse=True)
def external_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fake site's name must never reach a real resolver; the guard has tests of its own."""
    monkeypatch.setattr(SourceHostGuard, "require_public", lambda url, allowed_hosts, allow_list_variable: None)


@pytest.fixture
def confluence(world: World, monkeypatch: pytest.MonkeyPatch) -> FakeConfluence:
    fake = FakeConfluence(page_size=2)
    fake.add_page("1", "Engineering")
    fake.add_page("2", "Runbooks", ancestors=[("1", "Engineering")])
    fake.add_page("3", "Deploy", ancestors=[("1", "Engineering"), ("2", "Runbooks")], labels=["runbook"])
    fake.add_page("4", "Rollback", ancestors=[("1", "Engineering"), ("2", "Runbooks")])
    fake.add_page("10", "Operations", space="OPS")
    fake.install(monkeypatch)
    _configure(world, space_keys=["ENG", "OPS"])
    world.rows["wiki-db"] = MagicMock(source="structured", deleting=False)
    return fake


def _configure(world: World, **changes: object) -> None:
    options = {
        "base_url": SITES["cloud"],
        "email": "bot@acme.test",
        "api_token": "s3cret-token",
        "space_keys": ["ENG", "OPS"],
        **changes,
    }
    world.configs["wiki-db"] = StructuredSyncConfig.model_validate({"source_kind": "confluence", "confluence": options})


def _bodies_read(confluence: FakeConfluence, since: int) -> set[str]:
    """IDs of the pages whose body was fetched by the requests sent after ``since``."""
    searches = confluence.searches()[since:]
    return {
        page_id.strip()
        for search in searches
        if (ids := _ID_LIST.match(search["cql"]))
        for page_id in ids.group(1).split(",")
    }


class TestConfluenceSync:
    def test_a_first_sync_writes_every_page_with_its_tree_as_folders(self, world: World, confluence: FakeConfluence):
        result = world.sync("wiki-db", asset=_ASSET)

        assert result.success
        assert world.files("wiki-db") == _TREE
        deploy = world.body("wiki-db", "ENG/Engineering/Runbooks/Deploy.md")
        assert "url: https://acme.atlassian.net/wiki/spaces/ENG/pages/3\n" in deploy
        assert "\n# Deploy\n\nBody\n" in deploy

    def test_a_second_sync_of_unchanged_pages_reads_no_body_and_writes_nothing(
        self, world: World, confluence: FakeConfluence
    ):
        world.sync("wiki-db", asset=_ASSET)
        writes, searches = world.file_writes(), len(confluence.searches())

        result = world.sync("wiki-db", asset=_ASSET)

        assert result.success
        assert world.file_writes() == writes
        assert _bodies_read(confluence, since=searches) == set()
        assert world.step_metadata(result, "sync_structured_records")["Files written"] == 0

    def test_an_edited_page_is_the_only_one_read_and_rewritten(self, world: World, confluence: FakeConfluence):
        world.sync("wiki-db", asset=_ASSET)
        writes, searches = world.file_writes(), len(confluence.searches())
        confluence.edit("3", "<p>Run make deploy twice.</p>")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert _bodies_read(confluence, since=searches) == {"3"}
        assert world.file_writes() == writes + 1
        assert "Run make deploy twice." in world.body("wiki-db", "ENG/Engineering/Runbooks/Deploy.md")

    def test_renaming_a_page_moves_its_children_in_the_same_run_and_leaves_no_stale_file(
        self, world: World, confluence: FakeConfluence
    ):
        """The children keep their versions; a last-modified cursor would leave them missing until a full re-read."""
        world.sync("wiki-db", asset=_ASSET)
        searches = len(confluence.searches())
        confluence.rename("2", "Playbooks")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert world.files("wiki-db") == [
            "ENG/Engineering.md",
            "ENG/Engineering/Playbooks.md",
            "ENG/Engineering/Playbooks/Deploy.md",
            "ENG/Engineering/Playbooks/Rollback.md",
            "OPS/Operations.md",
        ]
        assert _bodies_read(confluence, since=searches) == {"2", "3", "4"}
        assert world.announced(world.removed_events) == [
            "ENG/Engineering/Runbooks.md",
            "ENG/Engineering/Runbooks/Deploy.md",
            "ENG/Engineering/Runbooks/Rollback.md",
        ]

    def test_a_moved_page_is_found_although_no_version_changed(self, world: World, confluence: FakeConfluence):
        world.sync("wiki-db", asset=_ASSET)
        confluence.move("3", "1")

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "ENG/Engineering/Deploy.md" in world.files("wiki-db")
        assert "ENG/Engineering/Runbooks/Deploy.md" not in world.files("wiki-db")

    def test_a_relabelled_page_is_read_again_although_no_version_changed(
        self, world: World, confluence: FakeConfluence
    ):
        world.sync("wiki-db", asset=_ASSET)
        writes, searches = world.file_writes(), len(confluence.searches())
        confluence.relabel("3", ["runbook", "deprecated"])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert _bodies_read(confluence, since=searches) == {"3"}
        assert world.file_writes() == writes + 1
        assert "labels:\n- deprecated\n- runbook\n" in world.body("wiki-db", "ENG/Engineering/Runbooks/Deploy.md")

    @pytest.mark.parametrize("change", ["delete", "archive"])
    def test_a_deleted_or_archived_page_is_removed(self, world: World, confluence: FakeConfluence, change: str):
        world.sync("wiki-db", asset=_ASSET)
        if change == "delete":
            confluence.remove("4")
        else:
            confluence.page("4")["status"] = "archived"

        assert world.sync("wiki-db", asset=_ASSET).success

        assert "ENG/Engineering/Runbooks/Rollback.md" not in world.files("wiki-db")
        assert world.announced(world.removed_events) == ["ENG/Engineering/Runbooks/Rollback.md"]

    def test_rejected_credentials_fail_the_sync_and_remove_nothing(self, world: World, confluence: FakeConfluence):
        world.sync("wiki-db", asset=_ASSET)
        confluence.fail_next(401, {"message": "Unauthorized"})

        result = world.sync("wiki-db", asset=_ASSET)

        assert not result.success
        [failure] = result.get_step_failure_events()
        shown_on_the_run_page = failure.event_specific_data.error.to_string()
        assert f"ValueError: Confluence rejected the credentials for {SITES['cloud']} (401)" in shown_on_the_run_page
        assert "s3cret-token" not in shown_on_the_run_page
        assert world.files("wiki-db") == _TREE

    def test_a_space_the_account_cannot_see_fails_instead_of_emptying_it(
        self, world: World, confluence: FakeConfluence
    ):
        """Confluence answers a search in an unreadable space with no pages; the listing would remove all of its."""
        world.sync("wiki-db", asset=_ASSET)
        confluence.spaces.discard("OPS")

        result = world.sync("wiki-db", asset=_ASSET)

        assert not result.success
        [failure] = result.get_step_failure_events()
        assert "Confluence space OPS does not exist, or Sync Bot cannot see it." in (
            failure.event_specific_data.error.to_string()
        )
        assert world.files("wiki-db") == _TREE

    def test_adding_a_space_reads_everything_again(self, world: World, confluence: FakeConfluence):
        _configure(world, space_keys=["ENG"])
        world.sync("wiki-db", asset=_ASSET)
        searches = len(confluence.searches())
        _configure(world, space_keys=["ENG", "OPS"])

        assert world.sync("wiki-db", asset=_ASSET).success

        assert _bodies_read(confluence, since=searches) == {"1", "2", "3", "4", "10"}
