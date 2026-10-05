import tempfile
from pathlib import Path
from typing import Annotated

import dlt
from dagster import DagsterRunStatus, OpDefinition, OpExecutionContext, Output, RunsFilter, op
from dagster_dlt import DagsterDltResource
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext
from mongoengine import DoesNotExist
from swiss_ai_hub.core.persistence import BucketEntity

from swiss_ai_hub.pipeline.resources.structured.markdown_data_lake_destination import MarkdownDataLakeDestination
from swiss_ai_hub.pipeline.resources.structured.structured_source_state_store import StructuredSourceStateStore
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.types.structured_sync_outcome import StructuredSyncOutcome
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection
from swiss_ai_hub.pipeline.util.run_routing import BUCKET_RUN_TAG, bucket_from_run_tag
from swiss_ai_hub.pipeline.util.source_builders import source_config_for_bucket

_RUNNING = [DagsterRunStatus.STARTING, DagsterRunStatus.STARTED]


def sync_structured_records_op(
    source: Annotated[str, "Source pipeline id this code location runs as"],
    config_type: Annotated[type[StructuredSyncConfig], "Config class a database's source configuration is read as"],
) -> OpDefinition:
    """The step that writes one database's changed records to its data lake, the database taken from the run tag.

    The cursor is restored before and saved after a run that succeeded end to end, and the dlt pipeline is
    deactivated afterwards: every step of a run shares this process, and a later step must never read its cursor.
    """

    @op(name=f"{source}_sync_structured_records", code_version="v1")
    def sync_structured_records(
        context: OpExecutionContext, dagster_dlt: DagsterDltResource
    ) -> Output[StructuredSyncOutcome]:
        bucket = bucket_from_run_tag(context)
        _refuse_a_second_sync_of(context, bucket)
        config = source_config_for_bucket(bucket, source, config_type)
        fingerprint = config.scope_fingerprint()
        store = StructuredSourceStateStore(source, bucket)
        destination = MarkdownDataLakeDestination(bucket, context)
        with tempfile.TemporaryDirectory(prefix="dlt-") as pipelines_dir:
            pipeline_dir = Path(pipelines_dir) / f"{source}_{bucket}"
            restored = store.restore(pipeline_dir, fingerprint)
            rows_loaded = _run(context, dagster_dlt, config, destination, pipelines_dir, pipeline_dir.name)
            if _still_filled_by(bucket, source):
                store.save(pipeline_dir, fingerprint)
            else:
                context.log.warning(f"'{bucket}' left source '{source}' during the sync; its state is not kept.")
        return Output(
            StructuredSyncOutcome(written_keys=destination.written_keys, scope_fingerprint=fingerprint),
            metadata={
                "Files written": len(destination.written_keys),
                "Files unchanged": destination.unchanged_count,
                "Rows loaded": rows_loaded,
                "Resumed from stored state": restored,
            },
        )

    return sync_structured_records


def _run(
    context: OpExecutionContext,
    dagster_dlt: DagsterDltResource,
    config: StructuredSyncConfig,
    destination: MarkdownDataLakeDestination,
    pipelines_dir: str,
    pipeline_name: str,
) -> int:
    """Runs the adapter's source into the markdown destination and returns how many rows dlt loaded.

    dagster-dlt reports a materialization per dlt resource, an asset every database would share, so its events are
    folded into this step's metadata instead of being emitted.
    """
    try:
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name,
            pipelines_dir=pipelines_dir,
            destination=destination.as_dlt_destination(),
            dataset_name=pipeline_name,
        )
        pipeline.config.restore_from_destination = False
        events = list(
            dagster_dlt.run(
                context=context, dlt_source=config.adapter().file_source(config.options()), dlt_pipeline=pipeline
            )
        )
    finally:
        Container()[PipelineContext].deactivate()
    return sum(event.metadata["rows_loaded"].value for event in events if "rows_loaded" in event.metadata)


def _refuse_a_second_sync_of(context: OpExecutionContext, bucket: str) -> None:
    """Two syncs of one database would race on its state, so a run gives way to any other sync of it already running.

    Creation order decides nothing: an earlier run can still be queued when a later one starts, and would then find
    only a later run. Two runs that check in the same instant both give way, and the next scheduled run syncs.
    """
    running = context.instance.get_run_records(
        RunsFilter(job_name=context.job_name, statuses=_RUNNING, tags={BUCKET_RUN_TAG: bucket})
    )
    others = [record for record in running if record.dagster_run.run_id != context.run_id]
    if others:
        raise RuntimeError(f"Run {others[0].dagster_run.run_id} is already syncing '{bucket}'.")


def _still_filled_by(bucket: str, source: str) -> bool:
    ensure_main_db_connection()
    try:
        entity = BucketEntity.get_bucket_by_bucket_name(bucket)
    except DoesNotExist:
        return False
    return entity.source == source and not entity.deleting
