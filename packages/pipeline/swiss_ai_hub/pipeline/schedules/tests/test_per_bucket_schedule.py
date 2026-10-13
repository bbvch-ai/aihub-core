from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from dagster import RunRequest, build_schedule_context, job, op

from swiss_ai_hub.pipeline.schedules.per_bucket_schedule import per_bucket_observe_schedule
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG, owned_by_ingestor, owned_by_source

_MODULE = "swiss_ai_hub.pipeline.schedules.per_bucket_schedule"


@op
def _noop() -> None: ...


@job
def observe_job() -> None:
    _noop()


def _bucket(
    name: str, *, ingestor: str = "document_ingestion", source: str | None = None, deleting: bool = False
) -> MagicMock:
    return MagicMock(bucket_name=name, ingestor=ingestor, source=source, deleting=deleting)


def _fan_out(owns) -> list[str]:
    schedule = per_bucket_observe_schedule(observe_job, owns=owns, hour=22)
    buckets = [
        _bucket("manual"),
        _bucket("synced", source="rclone"),
        _bucket("othersource", source="acme_sync"),
        _bucket("deleting", source="rclone", deleting=True),
        _bucket("legacy", ingestor="default_rag"),
    ]
    with patch(f"{_MODULE}.ensure_main_db_connection"), patch(f"{_MODULE}.BucketEntity") as bucket_cls:
        bucket_cls.get_all_buckets.return_value = buckets
        requests = list(
            schedule.evaluate_tick(
                build_schedule_context(scheduled_execution_time=datetime(2026, 9, 9, 22, tzinfo=UTC))
            ).run_requests
        )
    assert all(isinstance(request, RunRequest) for request in requests)
    return [request.tags[BUCKET_RUN_TAG] for request in requests]


class TestFanOut:
    def test_a_source_pipeline_observes_only_the_live_databases_it_fills(self):
        assert _fan_out(owned_by_source("rclone")) == ["synced"]

    def test_an_ingestion_pipeline_observes_only_the_live_databases_it_processes(self):
        assert _fan_out(owned_by_ingestor("document_ingestion")) == ["manual", "synced", "othersource"]
