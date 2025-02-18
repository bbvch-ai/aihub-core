from typing import Optional

from dagster import JobDefinition, RunConfig, define_asset_job, observable_source_asset


def materialize_all_job(
    namespace_name: str, config: Optional[RunConfig] = None
) -> JobDefinition:  # TODO: maybe remove namespace_name
    """Job that materializes all assets. This is useful when you have no partitioning. When you
    have partitions, starting this job will prompt you to specify the partition to materialize.
    However, in most cases, we use dynamic partitioning and let an op decide on which partitions even exist, hence,
    in many cases, you can't name the partitions a-priori.
    If you see yourself in that situation, you should use the `observe_source_job` instead.
    """
    return define_asset_job(name=f"{namespace_name}_materialize_all", config=config)


def observe_source_job(
    observable_asset: observable_source_asset,
    namespace_name: str,  # TODO: maybe remove namespace_name
    config: Optional[RunConfig] = None,
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
        name=f"{namespace_name}_{job_name}",
        config=config,
        description=job_description,
    )
