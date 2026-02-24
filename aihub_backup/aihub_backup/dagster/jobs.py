import dagster as dg

from aihub_backup.dagster.assets import create_backup
from aihub_backup.dagster.ops.restore_ops import run_full_restore, run_single_service_restore

backup_asset_job = dg.define_asset_job(
    name="backup_asset_job",
    selection=[create_backup],
    description="Run a full system backup (all services) for a given date partition.",
)


@dg.job(name="full_restore_job", description="Restore all services from a backup.")
def full_restore_job() -> None:
    run_full_restore()


@dg.job(name="single_service_restore_job", description="Restore a single service from a backup.")
def single_service_restore_job() -> None:
    run_single_service_restore()
