import logging
from typing import Annotated

from dagster import DefaultSensorStatus, SensorDefinition, SensorEvaluationContext, SkipReason, sensor
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.partition_utils import bucket_of_composite_partition_key
from swiss_ai_hub.pipeline.util.source_builders import build_rclone_client, remote_name_for_bucket

logger = logging.getLogger(__name__)

_CLEANUP_INTERVAL_SECONDS = 300


def source_bucket_cleanup_sensor(
    *,
    source: Annotated[str, "Source pipeline id this code location runs as"],
    partition_registry_name: Annotated[str, "The pipeline's dynamic-partition registry"],
) -> SensorDefinition:
    """Forgets databases this pipeline no longer fills: their partitions and their remote in the rclone daemon.

    Convergent rather than event-driven, like the knowledge teardown sensor: whatever still has partitions but no
    live row pointing at this source is still owed a cleanup. Storage teardown stays with the ingestion pipeline;
    this only removes what the source pipeline itself created.
    """

    @sensor(
        minimum_interval_seconds=_CLEANUP_INTERVAL_SECONDS,
        default_status=DefaultSensorStatus.RUNNING,
        name=f"SourceBucketCleanupSensorFor_{source}",
        description="Drops partitions and rclone remotes of databases that left this source pipeline.",
    )
    def _sensor(context: SensorEvaluationContext) -> SkipReason:
        ensure_main_db_connection()
        partition_keys = context.instance.get_dynamic_partitions(partition_registry_name)
        buckets_with_partitions = {bucket_of_composite_partition_key(key) for key in partition_keys}
        stale = sorted(bucket for bucket in buckets_with_partitions if not _still_filled_by(bucket, source))

        for bucket in stale:
            prefix = f"{bucket}|"
            for key in partition_keys:
                if key.startswith(prefix):
                    context.instance.delete_dynamic_partition(partition_registry_name, key)
            build_rclone_client().delete_remote(remote_name_for_bucket(bucket, source))
            context.log.info(f"Forgot '{bucket}': partitions and rclone remote removed")

        return SkipReason(f"{len(stale)} stale database(s) cleaned up.")

    return _sensor


def _still_filled_by(bucket: str, source: str) -> bool:
    try:
        entity = BucketEntity.get_bucket_by_bucket_name(bucket)
    except DoesNotExist:
        return False
    return entity.source == source and not entity.deleting
