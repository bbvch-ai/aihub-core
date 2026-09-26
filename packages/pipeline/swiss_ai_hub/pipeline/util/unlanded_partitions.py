from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated

from dagster import (
    AssetKey,
    AssetPartitionStatus,
    AssetRecordsFilter,
    DagsterEventType,
    DagsterInstance,
    DynamicPartitionsDefinition,
    RunsFilter,
)
from dagster._core.storage.dagster_run import FINISHED_STATUSES, RunRecord
from dagster._core.storage.tags import PARTITION_NAME_TAG

from swiss_ai_hub.pipeline.util.unlanded_partition_retry import UnlandedPartitionRetry
from swiss_ai_hub.pipeline.util.unlanded_partition_retry_config import UnlandedPartitionRetryConfig
from swiss_ai_hub.pipeline.util.unlanded_partitions_report import UnlandedPartitionsReport


class UnlandedPartitions:
    """Finds the partitions of an eagerly automated asset that were attempted but never landed.

    ``eager()`` counts a failed launch as handled and an unchanged upstream data version is not an update, so such a
    partition is never requested again until its source changes. Only partitions that already had a run are
    candidates: a new one is ``eager()``'s ``newly_missing`` case, and requesting it here would launch it twice.
    """

    @staticmethod
    def find(
        instance: DagsterInstance,
        config: UnlandedPartitionRetryConfig,
        partitions: DynamicPartitionsDefinition,
        partition_keys: Annotated[Sequence[str], "Keys to inspect, typically one database's"],
        now: datetime,
    ) -> UnlandedPartitionsReport:
        candidates, in_progress = UnlandedPartitions._candidates(instance, config.asset_key, partitions, partition_keys)
        last_success = UnlandedPartitions._last_success_timestamps(instance, config.asset_key, candidates)
        retry_runs = UnlandedPartitions._retry_runs_by_key(instance, config.retry_job_name, candidates)

        report = UnlandedPartitionsReport(in_progress=in_progress)
        for key in candidates:
            UnlandedPartitions._classify(report, key, retry_runs[key], last_success.get(key), config, now)
        return report

    @staticmethod
    def _candidates(
        instance: DagsterInstance,
        asset_key: AssetKey,
        partitions: DynamicPartitionsDefinition,
        partition_keys: Sequence[str],
    ) -> tuple[list[str], list[str]]:
        """A missing partition with a planned materialization had a run that ended without landing, e.g. a canceled
        one; Dagster reports it as neither failed nor in progress."""
        if not partition_keys:
            return [], []
        statuses = instance.get_status_by_partition(asset_key, partition_keys, partitions) or {}
        attempted = instance.get_latest_storage_id_by_partition(
            asset_key, DagsterEventType.ASSET_MATERIALIZATION_PLANNED, set(partition_keys)
        )
        candidates: list[str] = []
        in_progress: list[str] = []
        for key in partition_keys:
            match statuses.get(key):
                case AssetPartitionStatus.IN_PROGRESS:
                    in_progress.append(key)
                case AssetPartitionStatus.FAILED:
                    candidates.append(key)
                case None if key in attempted:
                    candidates.append(key)
        return candidates, in_progress

    @staticmethod
    def _last_success_timestamps(
        instance: DagsterInstance, asset_key: AssetKey, partition_keys: list[str]
    ) -> dict[str, float]:
        """A failed partition may have landed before its source changed; attempts count from that success on."""
        if not partition_keys:
            return {}
        storage_ids = instance.get_latest_storage_id_by_partition(
            asset_key, DagsterEventType.ASSET_MATERIALIZATION, set(partition_keys)
        )
        if not storage_ids:
            return {}
        records = instance.fetch_materializations(
            AssetRecordsFilter(asset_key=asset_key, storage_ids=list(storage_ids.values())), limit=len(storage_ids)
        ).records
        return {record.partition_key: record.timestamp for record in records if record.partition_key is not None}

    @staticmethod
    def _retry_runs_by_key(
        instance: DagsterInstance, retry_job_name: str, partition_keys: list[str]
    ) -> defaultdict[str, list[RunRecord]]:
        """Newest first, in one query for every key rather than one per key."""
        runs_by_key: defaultdict[str, list[RunRecord]] = defaultdict(list)
        if not partition_keys:
            return runs_by_key
        for record in instance.get_run_records(
            RunsFilter(job_name=retry_job_name, tags={PARTITION_NAME_TAG: partition_keys})
        ):
            runs_by_key[record.dagster_run.tags[PARTITION_NAME_TAG]].append(record)
        return runs_by_key

    @staticmethod
    def _classify(
        report: UnlandedPartitionsReport,
        key: str,
        retry_runs: list[RunRecord],
        last_success: float | None,
        config: UnlandedPartitionRetryConfig,
        now: datetime,
    ) -> None:
        if any(run.dagster_run.status not in FINISHED_STATUSES for run in retry_runs):
            report.in_progress.append(key)
            return
        attempts = [
            run for run in retry_runs if last_success is None or UnlandedPartitions._began_at(run) > last_success
        ]
        if len(attempts) >= config.max_attempts:
            report.exhausted.append(key)
            return
        if attempts and UnlandedPartitions._backing_off(attempts[0], len(attempts), config, now):
            report.backing_off.append(key)
            return
        report.to_retry.append(
            UnlandedPartitionRetry(partition_key=key, attempt=len(attempts) + 1, run_number=len(retry_runs))
        )

    @staticmethod
    def _backing_off(
        latest_attempt: RunRecord, attempts: int, config: UnlandedPartitionRetryConfig, now: datetime
    ) -> bool:
        ended_at = latest_attempt.end_time or latest_attempt.update_timestamp.timestamp()
        wait = config.base_delay * 2 ** (attempts - 1)
        return now.timestamp() - ended_at < wait.total_seconds()

    @staticmethod
    def _began_at(run: RunRecord) -> float:
        """The start event's timestamp is as precise as the materialization's; the creation column may be coarser,
        which would misplace a run created in the same second as the success it follows."""
        return run.start_time or run.create_timestamp.timestamp()
