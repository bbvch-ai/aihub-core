from dagster import AssetSelection, JobDefinition, RunConfig, define_asset_job, observable_source_asset
from dagster._core.storage.tags import PRIORITY_TAG

# Observation and removal are cheap steps whose results authorize the per-document ingestion runs,
# so they must not queue behind them. Every run defaults to priority 0, which collapses
# QueuedRunCoordinator's priority sort into plain FIFO; a bulk upload then leaves an observation
# waiting behind hundreds of already-queued ingestion runs. The sort spans the whole queue rather
# than one page, so this jumps the backlog outright without reserving any capacity.
ORCHESTRATION_RUN_PRIORITY = {PRIORITY_TAG: "10"}


def materialize_all_job(namespace_name: str, config: RunConfig | None = None) -> JobDefinition:
    """Job that materializes all assets. This is useful when you have no partitioning. When you
    have partitions, starting this job will prompt you to specify the partition to materialize.
    However, in most cases, we use dynamic partitioning and let an op decide on which partitions even exist, hence,
    in many cases, you can't name the partitions a-priori.
    If you see yourself in that situation, you should use the `observe_source_job` instead.
    """
    return define_asset_job(name=f"{namespace_name}_materialize_all", config=config)


def observe_source_job(
    observable_asset: observable_source_asset,
    source_location_name: str,
    config: RunConfig | None = None,
    job_name: str = "source_observation",
    job_description: str = "Job that observes a source asset",
) -> JobDefinition:
    """Job that observes a source asset. This is useful when you want to observe a source asset
    that determines the dynamic partitions. As the job only triggers the observation asset and not the materialization
    of all partitioned assets, it will not ask you to specify the partition keys.
    However, make sure that you have auto-materialization rules specified for all downstream assets to ensure
    that the downstream asset will materialize themselves when they note any change in the partitioning reported
    by the observable asset.
    """
    return define_asset_job(
        selection=[observable_asset],
        name=f"{source_location_name}_{job_name}",
        config=config,
        description=job_description,
        run_tags=ORCHESTRATION_RUN_PRIORITY,
    )


def materialize_asset_job(
    source_location_name: str,
    job_name: str,
    asset_selection: AssetSelection,
    config: RunConfig | None = None,
    description: str | None = None,
) -> JobDefinition:
    """Creates a job that materializes a specific selection of assets."""
    return define_asset_job(
        name=f"{source_location_name}_{job_name}",
        selection=asset_selection,
        config=config,
        description=description or "A job to materialize the selected assets.",
        run_tags=ORCHESTRATION_RUN_PRIORITY,
    )
