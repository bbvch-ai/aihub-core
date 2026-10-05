from pathlib import Path
from unittest.mock import MagicMock, patch

import dlt
import pytest
from dagster import build_op_context

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.resources.structured.markdown_data_lake_destination import MarkdownDataLakeDestination
from swiss_ai_hub.pipeline.resources.structured.tests.fake_s3_client import FakeS3Client
from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import (
    FAKE_TRACKERS,
    FakeStructuredSyncConfig,
    fake_issue,
)

_MODULE = "swiss_ai_hub.pipeline.resources.structured.markdown_data_lake_destination"
_BUCKET = "db-a"
_TRACKER = "https://tracker.test/a"


@pytest.fixture
def s3() -> FakeS3Client:
    return FakeS3Client()


@pytest.fixture
def notify(s3: FakeS3Client):
    def client(bucket: str, **_) -> S3DataLakeClient:
        return S3DataLakeClient(bucket, s3, False)

    with (
        patch(f"{_MODULE}.build_s3_data_lake_client", side_effect=client),
        patch(f"{_MODULE}.notify_source_updated") as notify_source_updated,
    ):
        yield notify_source_updated


@pytest.fixture(autouse=True)
def tracker() -> list[dict]:
    FAKE_TRACKERS[_TRACKER] = [
        fake_issue("ABC", "ABC-1", "2026-09-01T10:00:00Z"),
        fake_issue("XYZ", "XYZ-1", "2026-09-02T10:00:00Z"),
    ]
    return FAKE_TRACKERS[_TRACKER]


def _sync(pipelines_dir: Path) -> MarkdownDataLakeDestination:
    """One sync of the fake tracker into the bucket, the way the pipeline will run it per database."""
    config = FakeStructuredSyncConfig.model_validate(
        {"source_kind": "fake_tracker", "fake_tracker": {"base_url": _TRACKER}}
    )
    with build_op_context() as context:
        destination = MarkdownDataLakeDestination(_BUCKET, context)
        pipeline = dlt.pipeline(
            pipeline_name=f"structured_{_BUCKET}",
            pipelines_dir=str(pipelines_dir),
            destination=destination.as_dlt_destination(),
            dataset_name=_BUCKET,
        )
        pipeline.config.restore_from_destination = False
        pipeline.run(config.adapter().file_source(config.options())).raise_on_failed_jobs()
    return destination


def _announced(notify: MagicMock) -> list[str]:
    return [key for call in notify.call_args_list for key in call.args[1]]


class TestWrites:
    def test_new_records_land_as_markdown_files_and_are_announced(self, tmp_path, s3, notify):
        destination = _sync(tmp_path)

        assert s3.keys(_BUCKET) == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]
        stored = s3.objects[(_BUCKET, "ABC/ABC-1.md")]
        assert stored["ContentType"] == "text/markdown"
        assert stored["Body"].startswith(b"---\ntitle: Title of ABC-1\n")
        assert sorted(destination.written_keys) == sorted(_announced(notify)) == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]

    def test_a_second_run_with_nothing_new_writes_and_announces_nothing(self, tmp_path, s3, notify):
        _sync(tmp_path)
        puts_after_first_run = s3.put_attempts
        notify.reset_mock()

        destination = _sync(tmp_path)

        assert destination.written_keys == []
        assert s3.put_attempts == puts_after_first_run
        assert _announced(notify) == []

    def test_records_delivered_again_after_a_lost_state_are_not_rewritten(self, tmp_path, s3, notify):
        """dlt delivers at least once; comparing with each object's ETag is what makes a re-delivery a no-op."""
        _sync(tmp_path / "first")
        puts_after_first_run = s3.put_attempts
        notify.reset_mock()

        destination = _sync(tmp_path / "state_lost")

        assert destination.unchanged_count == 2
        assert s3.put_attempts == puts_after_first_run
        assert _announced(notify) == []

    def test_written_files_carry_no_metadata_of_their_own(self, tmp_path, s3, notify):
        """Ingestion copies a file's metadata into its document and embeds it with every chunk."""
        _sync(tmp_path)

        assert [s3.objects[(_BUCKET, key)]["Metadata"] for key in s3.keys(_BUCKET)] == [{}, {}]

    def test_an_edited_record_is_rewritten_alone(self, tmp_path, s3, notify, tracker):
        _sync(tmp_path)
        notify.reset_mock()
        tracker[0] = fake_issue("ABC", "ABC-1", "2026-09-10T10:00:00Z", body="Edited")

        destination = _sync(tmp_path)

        assert destination.written_keys == _announced(notify) == ["ABC/ABC-1.md"]
        assert s3.objects[(_BUCKET, "ABC/ABC-1.md")]["Body"].endswith(b"Edited\n")


class TestFailures:
    def test_a_refused_write_fails_the_run_at_once_instead_of_being_retried(self, tmp_path, s3, notify):
        s3.fail_next_puts_with = ["AccessDenied"]

        with pytest.raises(Exception, match="refused"):
            _sync(tmp_path)

        assert s3.put_attempts == 1
        assert _announced(notify) == []

    def test_a_passing_hiccup_is_retried_within_the_run(self, tmp_path, s3, notify):
        s3.fail_next_puts_with = ["SlowDown"]

        _sync(tmp_path)

        assert s3.keys(_BUCKET) == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]
