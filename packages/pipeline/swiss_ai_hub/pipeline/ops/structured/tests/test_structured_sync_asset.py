"""Real syncs of the structured asset, in process: dlt runs for real, every system around it is faked."""

import json
from typing import Annotated, ClassVar
from unittest.mock import MagicMock, patch

import pytest
from dagster import AssetKey, DagsterInstance, DagsterRun, DagsterRunStatus, ExecuteInProcessResult, materialize
from dagster_dlt import DagsterDltResource
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext
from mongoengine import DoesNotExist
from pydantic import Field

from swiss_ai_hub.pipeline.assets.factories.structured_to_data_lake.structured_sync_factory import (
    structured_sync_factory,
)
from swiss_ai_hub.pipeline.ops.structured.sync_structured_records import _refuse_a_second_sync_of
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.resources.structured.tests.fake_s3_client import FakeS3Client
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import (
    FAKE_ATTACHMENTS,
    FAKE_DOWNLOADS,
    FAKE_TRACKERS,
    FakeStructuredSyncConfig,
    FakeTrackerAdapter,
    FakeTrackerOptions,
    fake_issue,
)
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG

_KEY = AssetKey(["structured_source_to_datalake", "records"])
_STATE_KEY = ".structured_dagster/state.json"
_OPS = "swiss_ai_hub.pipeline.ops"
_STRUCTURED = "swiss_ai_hub.pipeline.resources.structured"


class FakeTrackerListedThroughDlt(FakeTrackerAdapter):
    """Lists by iterating its own incremental resource, as a real adapter reusing its dlt source might, and notes
    whether a dlt pipeline was still active when it did."""

    pipeline_active_while_listing: ClassVar[list[bool]] = []

    def list_record_paths(self, options: FakeTrackerOptions) -> set[str]:
        self.pipeline_active_while_listing.append(Container()[PipelineContext].is_active())
        return {
            StructuredRecordFile.object_key_for(record["project"], [record["key"]])
            for record in self.dlt_source(options)
        }


class ListedThroughDltConfig(StructuredSyncConfig):
    fake_tracker: Annotated[FakeTrackerOptions, Field(description="Fake tracker options.")] = Field(
        default_factory=FakeTrackerOptions
    )

    @classmethod
    def adapters(cls) -> list[type[AbstractStructuredSourceAdapter]]:
        return [FakeTrackerListedThroughDlt]


_ASSET = structured_sync_factory(_KEY, source="structured", config_type=FakeStructuredSyncConfig)
_LISTED_THROUGH_DLT = structured_sync_factory(_KEY, source="structured", config_type=ListedThroughDltConfig)


class World:
    """Everything outside the pipeline: the trackers, the databases' rows and configurations, S3 and the event bus."""

    def __init__(self) -> None:
        self.s3 = FakeS3Client()
        self.configs: dict[str, StructuredSyncConfig] = {}
        self.rows: dict[str, MagicMock] = {}
        self.written_events = MagicMock()
        self.removed_events = MagicMock()
        self.instance = DagsterInstance.ephemeral()

    def database(
        self, bucket: str, issues: list[dict], config_type: type[StructuredSyncConfig] = FakeStructuredSyncConfig
    ):
        url = f"https://tracker.test/{bucket}"
        FAKE_TRACKERS[url] = issues
        self.configs[bucket] = config_type.model_validate(
            {"source_kind": "fake_tracker", "fake_tracker": {"base_url": url, "project": "scope-1"}}
        )
        self.rows[bucket] = MagicMock(source="structured", deleting=False)
        return issues

    def sync(self, bucket: str, asset=_ASSET) -> ExecuteInProcessResult:
        return materialize(
            [asset],
            resources={"dagster_dlt": DagsterDltResource()},
            tags={BUCKET_RUN_TAG: bucket},
            instance=self.instance,
            raise_on_error=False,
        )

    def files(self, bucket: str) -> list[str]:
        return [key for key in self.s3.keys(bucket) if not key.startswith(".")]

    def body(self, bucket: str, key: str) -> str:
        return self.s3.objects[(bucket, key)]["Body"].decode()

    def state(self, bucket: str) -> bytes | None:
        return self.s3.objects.get((bucket, _STATE_KEY), {}).get("Body")

    def file_writes(self) -> int:
        return sum(1 for _, key in self.s3.put_keys if not key.startswith("."))

    def announced(self, events: MagicMock) -> list[str]:
        return sorted(key for call in events.call_args_list for key in call.args[1])

    @staticmethod
    def step_metadata(result: ExecuteInProcessResult, step: str) -> dict:
        [output] = [
            event.step_output_data
            for event in result.all_events
            if event.event_type_value == "STEP_OUTPUT" and event.step_key.endswith(step)
        ]
        return {name: value.value for name, value in output.metadata.items()}


@pytest.fixture
def world():
    world = World()

    def client(bucket: str, **_) -> S3DataLakeClient:
        return S3DataLakeClient(bucket, world.s3, False)

    def config(bucket: str, *_) -> StructuredSyncConfig:
        return world.configs[bucket]

    def row(bucket: str) -> MagicMock:
        if bucket not in world.rows:
            raise DoesNotExist(bucket)
        return world.rows[bucket]

    with (
        patch(f"{_OPS}.structured.sync_structured_records.source_config_for_bucket", side_effect=config),
        patch(f"{_OPS}.structured.list_structured_record_paths.source_config_for_bucket", side_effect=config),
        patch(f"{_OPS}.structured.sync_structured_records.ensure_main_db_connection"),
        patch(f"{_OPS}.structured.sync_structured_records.BucketEntity") as bucket_entity,
        patch(f"{_OPS}.structured.reconcile_structured_bucket.build_s3_data_lake_client", side_effect=client),
        patch(f"{_OPS}.source.routed.delete_data_lake_files_from_bucket.build_s3_data_lake_client", side_effect=client),
        patch(f"{_OPS}.source.routed.announce_removed_files.notify_source_updated", world.removed_events),
        patch(f"{_STRUCTURED}.structured_data_lake_destination.build_s3_data_lake_client", side_effect=client),
        patch(f"{_STRUCTURED}.structured_data_lake_destination.notify_source_updated", world.written_events),
        patch(f"{_STRUCTURED}.structured_source_state_store.build_s3_data_lake_client", side_effect=client),
    ):
        bucket_entity.get_bucket_by_bucket_name.side_effect = row
        yield world


def _issue(project: str, key: str, day: int, body: str = "Body text") -> dict:
    return fake_issue(project, key, f"2026-09-{day:02}T10:00:00Z", body=body)


def _create_during_the_next_listing(monkeypatch: pytest.MonkeyPatch, issues: list[dict], issue: dict) -> None:
    """The record appears at the source after the sync fetched it but before the listing does."""
    list_record_paths = FakeTrackerAdapter.list_record_paths

    def created_in_the_gap(self, options):
        if issue not in issues:
            issues.append(issue)
        return list_record_paths(self, options)

    monkeypatch.setattr(FakeTrackerAdapter, "list_record_paths", created_in_the_gap)


class TestWrites:
    def test_two_databases_of_the_same_kind_never_share_files_or_state(self, world):
        world.database("db-a", [_issue("ABC", "ABC-1", 1, body="A's issue")])
        world.database("db-b", [_issue("ABC", "ABC-1", 2, body="B's issue"), _issue("XYZ", "XYZ-1", 3)])

        assert world.sync("db-a").success
        assert world.sync("db-b").success

        assert world.files("db-a") == ["ABC/ABC-1.md"]
        assert world.files("db-b") == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]
        assert "A's issue" in world.body("db-a", "ABC/ABC-1.md")
        assert "B's issue" in world.body("db-b", "ABC/ABC-1.md")
        assert world.state("db-a")
        assert world.state("db-b")
        assert world.state("db-a") != world.state("db-b")

    def test_a_rerun_with_nothing_new_writes_no_file_and_sends_no_event(self, world):
        world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("XYZ", "XYZ-1", 2)])
        world.sync("db-a")
        writes = world.file_writes()
        world.written_events.reset_mock()

        result = world.sync("db-a")

        assert result.success
        assert world.file_writes() == writes
        assert world.announced(world.written_events) == []
        assert world.announced(world.removed_events) == []
        sync = world.step_metadata(result, "sync_structured_records")
        assert sync["Resumed from stored state"] is True
        assert sync["Files unchanged"] == 0, "nothing was fetched at all, not merely skipped by hash"

    def test_a_failed_load_keeps_the_previous_state_and_the_next_run_catches_up(self, world):
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")
        before = world.state("db-a")
        issues[0] = _issue("ABC", "ABC-1", 5, body="Edited")
        world.s3.fail_next_puts_with = ["AccessDenied"]

        assert not world.sync("db-a").success
        assert world.state("db-a") == before

        assert world.sync("db-a").success
        assert world.body("db-a", "ABC/ABC-1.md").endswith("Edited\n")

    def test_a_namespace_with_a_space_survives_the_removal_that_follows_its_write(self, world):
        """The listing builds its keys through the same rules as the written file, or the removal would delete it."""
        world.database("db-a", [_issue("My Project", "MP-1", 1)])

        assert world.sync("db-a").success
        assert world.sync("db-a").success

        assert world.files("db-a") == ["My_Project/MP-1.md"]


class TestRemoval:
    def test_a_record_deleted_at_the_source_is_removed_and_announced_but_the_state_stays(self, world):
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("XYZ", "XYZ-1", 2)])
        world.sync("db-a")
        del issues[1]

        assert world.sync("db-a").success

        assert world.files("db-a") == ["ABC/ABC-1.md"]
        assert world.announced(world.removed_events) == ["XYZ/XYZ-1.md"]
        assert world.state("db-a") is not None

    def test_a_record_moved_to_another_project_leaves_no_stale_file(self, world):
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")
        issues[0] = _issue("XYZ", "ABC-1", 2)

        assert world.sync("db-a").success

        assert world.files("db-a") == ["XYZ/ABC-1.md"]

    def test_the_listing_runs_with_no_dlt_pipeline_left_active_by_the_sync(self, world):
        """Every step of a run shares one process: a listing iterating an incremental resource while the sync's
        pipeline is still active would resolve that pipeline's cursor and miss every older record."""
        FakeTrackerListedThroughDlt.pipeline_active_while_listing.clear()
        world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("ABC", "ABC-2", 2)], ListedThroughDltConfig)

        assert world.sync("db-a", _LISTED_THROUGH_DLT).success

        assert FakeTrackerListedThroughDlt.pipeline_active_while_listing == [False]
        assert world.files("db-a") == ["ABC/ABC-1.md", "ABC/ABC-2.md"]


class TestGuards:
    def test_a_file_written_by_this_run_is_never_removed_by_it_even_when_the_listing_misses_it(
        self, world, monkeypatch
    ):
        """An adapter that builds listed keys by hand lists "My Project/…" while "My_Project/…" was written."""
        world.database("db-a", [_issue("My Project", "MP-1", 1)])
        monkeypatch.setattr(
            FakeTrackerAdapter,
            "list_record_paths",
            lambda self, options: {
                f"{record['project']}/{record['key']}.md" for record in FAKE_TRACKERS[options.base_url]
            },
        )

        result = world.sync("db-a")

        assert result.success
        assert world.files("db-a") == ["My_Project/MP-1.md"]
        assert world.step_metadata(result, "reconcile_structured_bucket")["Written but not listed"] == 1

    def test_a_failing_listing_removes_nothing(self, world, monkeypatch):
        world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("XYZ", "XYZ-1", 2)])
        world.sync("db-a")

        def tracker_down(self, options):
            raise ConnectionError("tracker unreachable")

        monkeypatch.setattr(FakeTrackerAdapter, "list_record_paths", tracker_down)

        assert not world.sync("db-a").success
        assert world.files("db-a") == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]

    def test_an_empty_listing_never_empties_a_database(self, world, monkeypatch):
        """An API that answers 200 with nothing, after a lost permission, must not wipe what was synced."""
        world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")
        monkeypatch.setattr(FakeTrackerAdapter, "list_record_paths", lambda self, options: set())

        result = world.sync("db-a")

        assert not result.success
        assert world.files("db-a") == ["ABC/ABC-1.md"]
        failures = [event.step_failure_data.error.to_string() for event in result.get_step_failure_events()]
        assert any("refusing to empty" in failure for failure in failures)

    def test_a_configuration_edited_during_the_run_removes_nothing(self, world):
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("XYZ", "XYZ-1", 2)])
        world.sync("db-a")
        del issues[1]
        edited = FakeStructuredSyncConfig.model_validate(
            {"source_kind": "fake_tracker", "fake_tracker": {"base_url": "https://tracker.test/db-a", "project": "new"}}
        )

        with patch(f"{_OPS}.structured.list_structured_record_paths.source_config_for_bucket", return_value=edited):
            assert not world.sync("db-a").success

        assert world.files("db-a") == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]

    def test_a_record_missing_in_two_runs_in_a_row_makes_the_next_run_read_everything(self, world):
        """The cursor passed a record whose file is gone: only a full re-read writes it again."""
        world.database("db-a", [_issue("ABC", "ABC-1", 1), _issue("XYZ", "XYZ-1", 2)])
        world.sync("db-a")
        world.s3.delete_object(Bucket="db-a", Key="XYZ/XYZ-1.md")

        first = world.step_metadata(world.sync("db-a"), "reconcile_structured_bucket")
        assert (first["Listed records without a file"], first["State discarded"]) == (1, False)
        assert world.state("db-a") is not None

        second = world.step_metadata(world.sync("db-a"), "reconcile_structured_bucket")
        assert (second["Missing in two runs in a row"], second["State discarded"]) == (1, True)
        assert world.state("db-a") is None

        assert world.sync("db-a").success
        assert world.files("db-a") == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]

    def test_a_record_created_between_the_sync_and_the_listing_is_fetched_without_a_full_read(self, world, monkeypatch):
        """The listing sees a record the sync could not: the next incremental run fetches it, so no state is lost."""
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")
        _create_during_the_next_listing(monkeypatch, issues, _issue("ABC", "ABC-2", 5))

        gap = world.step_metadata(world.sync("db-a"), "reconcile_structured_bucket")
        assert (gap["Listed records without a file"], gap["State discarded"]) == (1, False)

        result = world.sync("db-a")
        assert world.step_metadata(result, "sync_structured_records")["Resumed from stored state"] is True
        assert world.step_metadata(result, "reconcile_structured_bucket")["Listed records without a file"] == 0
        assert world.files("db-a") == ["ABC/ABC-1.md", "ABC/ABC-2.md"]
        assert json.loads(world.state("db-a"))["missing_keys"] == []

    def test_different_records_missing_in_consecutive_runs_keep_the_state(self, world, monkeypatch):
        """A busy source creates a record in the gap of every run; each is fetched by the run after."""
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")

        for number, day in ((2, 5), (3, 6)):
            _create_during_the_next_listing(monkeypatch, issues, _issue("ABC", f"ABC-{number}", day))
            reconcile = world.step_metadata(world.sync("db-a"), "reconcile_structured_bucket")
            assert (reconcile["Listed records without a file"], reconcile["State discarded"]) == (1, False)

        assert world.state("db-a") is not None

    def test_a_second_sync_of_a_database_still_syncing_is_refused(self, world):
        world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.database("db-b", [_issue("ABC", "ABC-1", 1)])
        world.instance.add_run(
            DagsterRun(
                job_name="__ephemeral_asset_job__", status=DagsterRunStatus.STARTED, tags={BUCKET_RUN_TAG: "db-a"}
            )
        )

        assert not world.sync("db-a").success
        assert world.files("db-a") == []
        assert world.sync("db-b").success, "a sync of another database is no reason to wait"

    def test_a_sync_launched_from_the_asset_page_counts_as_a_sync_too(self, world):
        """The asset page runs the asset as ``__ASSET_JOB``, not as the sync job the schedule launches."""
        world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.instance.add_run(
            DagsterRun(
                job_name="__ASSET_JOB",
                asset_selection=frozenset({_KEY}),
                status=DagsterRunStatus.STARTED,
                tags={BUCKET_RUN_TAG: "db-a"},
            )
        )

        assert not world.sync("db-a").success
        assert world.files("db-a") == []

    @pytest.mark.parametrize(
        ("job_name", "asset_selection"),
        [
            ("document_ingestion_source_observation", None),
            ("__ASSET_JOB", frozenset({AssetKey(["document_ingestion_datalake_to_vectorstore", "documents"])})),
        ],
    )
    def test_an_ingestion_run_of_the_same_database_is_no_reason_to_wait(self, world, job_name, asset_selection):
        """Ingestion runs carry the database's bucket tag as well, and never touch the sync's state."""
        world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.instance.add_run(
            DagsterRun(
                job_name=job_name,
                asset_selection=asset_selection,
                status=DagsterRunStatus.STARTED,
                tags={BUCKET_RUN_TAG: "db-a"},
            )
        )

        assert world.sync("db-a").success
        assert world.files("db-a") == ["ABC/ABC-1.md"]

    def test_an_earlier_run_that_starts_after_a_later_one_gives_way_too(self):
        """A run queued first can be overtaken; starting next to the run that overtook it would race on the state."""
        own, later = MagicMock(), MagicMock()
        own.dagster_run.run_id, later.dagster_run.run_id = "own", "later"
        later.dagster_run.job_name = "structured_source_sync"
        context = MagicMock(run_id="own", job_name="structured_source_sync")
        context.instance.get_run_records.return_value = [own, later]

        with pytest.raises(RuntimeError, match="Run later is already syncing 'db-a'"):
            _refuse_a_second_sync_of(context, "db-a", _KEY)

        context.instance.get_run_records.return_value = [own]
        _refuse_a_second_sync_of(context, "db-a", _KEY)

    def test_a_database_that_left_the_source_during_the_sync_keeps_its_previous_state(self, world):
        issues = world.database("db-a", [_issue("ABC", "ABC-1", 1)])
        world.sync("db-a")
        before = world.state("db-a")
        issues.append(_issue("ABC", "ABC-2", 2))
        world.rows["db-a"].source = "rclone"

        world.sync("db-a")

        assert world.state("db-a") == before


class TestFiles:
    """A source offering files next to its records, run after run."""

    @pytest.fixture
    def attachments(self, world: World):
        world.database("db-files", [_issue("ABC", "ABC-1", 1)])
        FAKE_ATTACHMENTS["https://tracker.test/db-files"] = {"handbook.pdf": b"%PDF-1.7 v1"}
        FAKE_DOWNLOADS.clear()
        yield FAKE_ATTACHMENTS["https://tracker.test/db-files"]
        FAKE_ATTACHMENTS.pop("https://tracker.test/db-files")

    def test_an_unchanged_file_is_not_downloaded_again(self, world: World, attachments):
        assert world.sync("db-files").success
        downloads = len(FAKE_DOWNLOADS)

        assert world.sync("db-files").success

        assert world.files("db-files") == ["ABC/ABC-1.md", "Attachments/handbook.pdf"]
        assert len(FAKE_DOWNLOADS) == downloads == 1

    def test_a_changed_file_is_downloaded_and_rewritten(self, world: World, attachments):
        world.sync("db-files")
        attachments["handbook.pdf"] = b"%PDF-1.7 v2"

        assert world.sync("db-files").success

        assert world.s3.objects[("db-files", "Attachments/handbook.pdf")]["Body"] == b"%PDF-1.7 v2"

    def test_a_file_deleted_at_the_source_is_removed(self, world: World, attachments):
        world.sync("db-files")
        attachments.pop("handbook.pdf")

        assert world.sync("db-files").success

        assert world.files("db-files") == ["ABC/ABC-1.md"]
        assert world.announced(world.removed_events) == ["Attachments/handbook.pdf"]

    def test_a_file_the_source_refuses_is_tried_each_run_without_the_state_being_discarded(
        self, world: World, attachments
    ):
        """Counted as missing, it would discard the state after two runs and re-read the whole source."""
        attachments["secret.pdf"] = None

        results = [world.sync("db-files") for _ in range(3)]

        assert all(result.success for result in results)
        assert FAKE_DOWNLOADS.count("https://tracker.test/db-files/files/secret.pdf") == 3
        assert "Attachments/secret.pdf" not in world.files("db-files")
        assert [
            world.step_metadata(result, "reconcile_structured_bucket")["State discarded"] for result in results
        ] == [
            False,
            False,
            False,
        ]
        assert world.step_metadata(results[-1], "sync_structured_records")["Files not served by the source"] == 1

    def test_a_refused_file_is_written_once_the_source_serves_it(self, world: World, attachments):
        attachments["secret.pdf"] = None
        world.sync("db-files")
        attachments["secret.pdf"] = b"%PDF-1.7 released"

        assert world.sync("db-files").success

        assert "Attachments/secret.pdf" in world.files("db-files")
