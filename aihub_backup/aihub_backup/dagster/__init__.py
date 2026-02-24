import dagster as dg

from aihub_backup.dagster.assets import create_backup
from aihub_backup.dagster.jobs import backup_asset_job, full_restore_job, single_service_restore_job
from aihub_backup.dagster.resources import (
    BackupHandlersResource,
    BackupSettingsResource,
    DockerManagerResource,
    S3ManagerResource,
)
from aihub_backup.dagster.schedules import daily_backup_schedule

_settings = BackupSettingsResource()
_docker = DockerManagerResource()
_s3 = S3ManagerResource(settings=_settings)

defs = dg.Definitions(
    assets=[create_backup],
    jobs=[backup_asset_job, full_restore_job, single_service_restore_job],
    schedules=[daily_backup_schedule],
    resources={
        "backup_settings": _settings,
        "s3_manager": _s3,
        "docker_manager": _docker,
        "backup_handlers": BackupHandlersResource(settings=_settings, s3=_s3, docker=_docker),
    },
)
