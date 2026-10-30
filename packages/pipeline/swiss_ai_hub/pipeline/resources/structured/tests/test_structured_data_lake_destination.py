from pathlib import Path
from unittest.mock import MagicMock, patch

import dlt
import pytest
from dagster import build_op_context

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.resources.structured.structured_data_lake_destination import StructuredDataLakeDestination
from swiss_ai_hub.pipeline.resources.structured.tests.fake_s3_client import FakeS3Client
from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import (
    FAKE_ATTACHMENTS,
    FAKE_DOWNLOADS,
    FAKE_TRACKERS,
    FakeStructuredSyncConfig,
    fake_issue,
)

_MODULE = "swiss_ai_hub.pipeline.resources.structured.structured_data_lake_destination"
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


@pytest.fixture(autouse=True)
def attachments() -> dict[str, bytes | None]:
    FAKE_ATTACHMENTS[_TRACKER] = {}
    FAKE_DOWNLOADS.clear()
    yield FAKE_ATTACHMENTS[_TRACKER]
    FAKE_ATTACHMENTS.pop(_TRACKER)


def _sync(pipelines_dir: Path) -> StructuredDataLakeDestination:
    """One sync of the fake tracker into the bucket, the way the pipeline will run it per database."""
    config = FakeStructuredSyncConfig.model_validate(
        {"source_kind": "fake_tracker", "fake_tracker": {"base_url": _TRACKER}}
    )
    with build_op_context() as context:
        adapter, options = config.adapter(), config.options()
        destination = StructuredDataLakeDestination(
            _BUCKET, context, read_file=lambda reference: adapter.read_file(options, reference)
        )
        pipeline = dlt.pipeline(
            pipeline_name=f"structured_{_BUCKET}",
            pipelines_dir=str(pipelines_dir),
            destination=destination.as_dlt_destination(),
            dataset_name=_BUCKET,
        )
        pipeline.config.restore_from_destination = False
        pipeline.run(adapter.file_source(options)).raise_on_failed_jobs()
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

    def test_files_written_before_a_failing_write_are_still_announced(self, tmp_path, s3, notify):
        """A retry would find them unchanged, and nothing else would announce them before the daily observation."""
        s3.fail_next_puts_with = ["AccessDenied"]
        s3.succeed_puts_before_failing = 1

        with pytest.raises(Exception, match="refused"):
            _sync(tmp_path)

        assert len(s3.keys(_BUCKET)) == 1
        assert _announced(notify) == s3.keys(_BUCKET)

    def test_a_passing_hiccup_is_retried_within_the_run(self, tmp_path, s3, notify):
        s3.fail_next_puts_with = ["SlowDown"]

        _sync(tmp_path)

        assert s3.keys(_BUCKET) == ["ABC/ABC-1.md", "XYZ/XYZ-1.md"]


class TestFiles:
    def test_a_file_lands_under_its_own_extension_with_the_title_and_link_ingestion_reads(
        self, tmp_path, s3, notify, attachments
    ):
        attachments["Handbook 2026.pdf"] = b"%PDF-1.7 handbook"

        destination = _sync(tmp_path)

        stored = s3.objects[(_BUCKET, "Attachments/Handbook 2026.pdf")]
        assert stored["Body"] == b"%PDF-1.7 handbook"
        assert stored["ContentType"] == "application/pdf"
        assert stored["Metadata"] == {
            "document_title": "Handbook%202026.pdf",
            "source_origin": "https://tracker.test/a/attachments/Handbook%202026.pdf",
        }
        assert "Attachments/Handbook 2026.pdf" in destination.written_keys
        assert "Attachments/Handbook 2026.pdf" in _announced(notify)

    def test_a_file_delivered_again_after_a_lost_state_is_read_but_not_rewritten(
        self, tmp_path, s3, notify, attachments
    ):
        """Its ETag is the MD5 of the content, as for markdown, because a file is written in one part."""
        attachments["handbook.pdf"] = b"%PDF-1.7 handbook"
        _sync(tmp_path / "first")
        puts_after_first_run = s3.put_attempts
        notify.reset_mock()

        destination = _sync(tmp_path / "state_lost")

        assert destination.unchanged_count == 3
        assert s3.put_attempts == puts_after_first_run
        assert _announced(notify) == []

    def test_a_file_the_source_refuses_is_skipped_and_named_while_the_rest_is_written(
        self, tmp_path, s3, notify, attachments
    ):
        attachments["secret.pdf"] = None
        attachments["handbook.pdf"] = b"%PDF-1.7 handbook"

        destination = _sync(tmp_path)

        assert destination.failed_keys == ["Attachments/secret.pdf"]
        assert s3.keys(_BUCKET) == ["ABC/ABC-1.md", "Attachments/handbook.pdf", "XYZ/XYZ-1.md"]

    def test_a_file_without_anything_to_read_it_fails_at_once(self, tmp_path, s3, notify, attachments):
        attachments["handbook.pdf"] = b"%PDF-1.7 handbook"
        config = FakeStructuredSyncConfig.model_validate(
            {"source_kind": "fake_tracker", "fake_tracker": {"base_url": _TRACKER}}
        )
        with build_op_context() as context:
            pipeline = dlt.pipeline(
                pipeline_name=f"structured_{_BUCKET}",
                pipelines_dir=str(tmp_path),
                destination=StructuredDataLakeDestination(_BUCKET, context).as_dlt_destination(),
                dataset_name=_BUCKET,
            )
            pipeline.config.restore_from_destination = False

            source = config.adapter().file_source(config.options())
            with pytest.raises(Exception, match="nothing reads this source's files"):
                pipeline.run(source)
