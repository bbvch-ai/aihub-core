import json
from pathlib import Path
from unittest.mock import patch

import dlt
import pytest
from dagster import build_op_context

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.resources.structured.markdown_data_lake_destination import MarkdownDataLakeDestination
from swiss_ai_hub.pipeline.resources.structured.structured_source_state_store import StructuredSourceStateStore
from swiss_ai_hub.pipeline.resources.structured.tests.fake_s3_client import FakeS3Client
from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import (
    FAKE_TRACKERS,
    FakeStructuredSyncConfig,
    fake_issue,
)

_PACKAGE = "swiss_ai_hub.pipeline.resources.structured"
_TRACKER = "https://tracker.test/state"


@pytest.fixture
def s3() -> FakeS3Client:
    fake = FakeS3Client()

    def client(bucket: str, **_) -> S3DataLakeClient:
        return S3DataLakeClient(bucket, fake, False)

    with (
        patch(f"{_PACKAGE}.structured_source_state_store.build_s3_data_lake_client", side_effect=client),
        patch(f"{_PACKAGE}.markdown_data_lake_destination.build_s3_data_lake_client", side_effect=client),
        patch(f"{_PACKAGE}.markdown_data_lake_destination.notify_source_updated"),
    ):
        yield fake


def _working_dir_with_state(path: Path, cursor: str) -> Path:
    path.mkdir(parents=True)
    (path / "state.json").write_text(json.dumps({"sources": {"cursor": cursor}}))
    return path


class TestStore:
    def test_a_saved_state_is_restored_into_a_fresh_working_directory(self, tmp_path, s3):
        store = StructuredSourceStateStore("structured", "db-a")
        store.save(_working_dir_with_state(tmp_path / "run1", "2026-09-01"), "scope-1")

        assert store.restore(tmp_path / "run2", "scope-1") is True
        assert json.loads((tmp_path / "run2" / "state.json").read_text()) == {"sources": {"cursor": "2026-09-01"}}

    def test_there_is_nothing_to_restore_before_the_first_save(self, tmp_path, s3):
        assert StructuredSourceStateStore("structured", "db-a").restore(tmp_path / "run", "scope-1") is False
        assert not (tmp_path / "run" / "state.json").exists()

    def test_a_changed_scope_restores_nothing_so_the_run_reads_everything(self, tmp_path, s3):
        store = StructuredSourceStateStore("structured", "db-a")
        store.save(_working_dir_with_state(tmp_path / "run1", "2026-09-01"), "scope-1")

        assert store.restore(tmp_path / "run2", "scope-2") is False

    def test_two_databases_never_share_a_state(self, tmp_path, s3):
        StructuredSourceStateStore("structured", "db-a").save(_working_dir_with_state(tmp_path / "a", "x"), "scope")

        assert StructuredSourceStateStore("structured", "db-b").restore(tmp_path / "b", "scope") is False
        assert s3.keys("dagster") == ["structured/state/db-a.json"]

    def test_a_forgotten_database_has_no_state_left(self, tmp_path, s3):
        store = StructuredSourceStateStore("structured", "db-a")
        store.save(_working_dir_with_state(tmp_path / "run1", "x"), "scope")

        store.delete()

        assert s3.keys("dagster") == []


class TestResume:
    def test_a_restored_state_lets_a_new_process_skip_every_record_already_synced(self, tmp_path, s3):
        """Every Dagster step starts with an empty working directory; the stored state is all that carries the
        cursor from one run to the next."""
        FAKE_TRACKERS[_TRACKER] = [fake_issue("ABC", "ABC-1", "2026-09-01T10:00:00Z")]
        config = FakeStructuredSyncConfig.model_validate(
            {"source_kind": "fake_tracker", "fake_tracker": {"base_url": _TRACKER}}
        )
        store = StructuredSourceStateStore("structured", "db-a")

        first = _run(tmp_path / "first", config)
        store.save(tmp_path / "first" / "structured_db-a", config.scope_fingerprint())
        assert store.restore(tmp_path / "second" / "structured_db-a", config.scope_fingerprint())
        second = _run(tmp_path / "second", config)

        assert first.written_keys == ["ABC/ABC-1.md"]
        assert second.written_keys == []
        assert second.unchanged_count == 0, "nothing was even fetched, not merely skipped by hash"


def _run(pipelines_dir: Path, config: FakeStructuredSyncConfig) -> MarkdownDataLakeDestination:
    with build_op_context() as context:
        destination = MarkdownDataLakeDestination("db-a", context)
        pipeline = dlt.pipeline(
            pipeline_name="structured_db-a",
            pipelines_dir=str(pipelines_dir),
            destination=destination.as_dlt_destination(),
            dataset_name="db-a",
        )
        pipeline.config.restore_from_destination = False
        pipeline.run(config.adapter().file_source(config.options())).raise_on_failed_jobs()
    return destination
