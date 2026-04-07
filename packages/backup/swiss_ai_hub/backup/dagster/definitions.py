from dagster import AssetKey, Definitions

from swiss_ai_hub.backup.dagster.assets.backup_finalize_factory import backup_finalize_factory
from swiss_ai_hub.backup.dagster.assets.backup_session_factory import backup_session_factory
from swiss_ai_hub.backup.dagster.jobs.factory import backup_asset_job
from swiss_ai_hub.backup.dagster.resources.factory import backup_resources
from swiss_ai_hub.backup.dagster.schedules.factory import daily_backup_schedule


def backup_definitions() -> Definitions:
    session_key = AssetKey(["backup", "session"])
    finalize_key = AssetKey(["backup", "finalize"])

    session = backup_session_factory(session_key)
    finalize = backup_finalize_factory(finalize_key, session_key)
    backup_assets = [session, finalize]

    job = backup_asset_job(backup_assets)
    schedule = daily_backup_schedule(job)
    resources = backup_resources()

    return Definitions(
        assets=backup_assets,
        jobs=[job],
        schedules=[schedule],
        resources=resources,
    )
