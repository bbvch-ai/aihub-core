from dagster import AssetKey, Definitions

from swiss_ai_hub.backup.dagster.assets.backup_finalize_factory import backup_finalize_factory
from swiss_ai_hub.backup.dagster.assets.backup_session_factory import backup_session_factory
from swiss_ai_hub.backup.dagster.assets.restore_finalize_factory import restore_finalize_factory
from swiss_ai_hub.backup.dagster.assets.restore_service_factory import restore_service_factory
from swiss_ai_hub.backup.dagster.assets.restore_session_factory import restore_session_factory
from swiss_ai_hub.backup.dagster.jobs.factory import backup_asset_job, restore_asset_job
from swiss_ai_hub.backup.dagster.resources.factory import backup_resources
from swiss_ai_hub.backup.dagster.schedules.factory import daily_backup_schedule


def backup_definitions() -> Definitions:
    session_key = AssetKey(["backup", "session"])
    finalize_key = AssetKey(["backup", "finalize"])

    session = backup_session_factory(session_key)
    finalize = backup_finalize_factory(finalize_key, session_key)
    backup_assets = [session, finalize]

    restore_session_key = AssetKey(["restore", "session"])
    restore_service_keys = {
        "PostgreSQL": AssetKey(["restore", "postgres"]),
        "Milvus": AssetKey(["restore", "milvus"]),
        "Neo4j": AssetKey(["restore", "neo4j"]),
        "ClickHouse": AssetKey(["restore", "clickhouse"]),
        "Valkey": AssetKey(["restore", "valkey"]),
        "NATS": AssetKey(["restore", "nats"]),
    }
    restore_finalize_key = AssetKey(["restore", "finalize"])

    restore_session = restore_session_factory(restore_session_key)
    restore_service_assets = [
        restore_service_factory(key, restore_session_key, name, f"{name} restore")
        for name, key in restore_service_keys.items()
    ]
    restore_finalize = restore_finalize_factory(restore_finalize_key, restore_session_key, restore_service_keys)
    restore_assets = [restore_session, *restore_service_assets, restore_finalize]

    backup_job = backup_asset_job(backup_assets)
    restore_job = restore_asset_job(restore_assets)
    schedule = daily_backup_schedule(backup_job)

    resources = backup_resources()

    return Definitions(
        assets=[*backup_assets, *restore_assets],
        jobs=[backup_job, restore_job],
        schedules=[schedule],
        resources=resources,
    )
