from dagster import JobDefinition, job

from swiss_ai_hub.pipeline.ops.repair.repair_orphaned_nodes_op import repair_orphaned_nodes_op


def repair_orphaned_nodes_job(*, source_location_name: str) -> JobDefinition:
    """One-op job that deletes the vector nodes a failed removal left behind in one knowledge database.

    Launched by hand with the ``aihub/bucket`` run tag and never scheduled: it scans every partition the
    database's namespaces use, which is too expensive to run after each removal.
    """

    @job(
        name=f"{source_location_name}_repair_orphaned_nodes",
        description="Deletes vector nodes whose document is gone. Dry run unless run config sets dry_run: false.",
    )
    def _job() -> None:
        repair_orphaned_nodes_op()

    return _job
