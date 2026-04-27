from dagster import AssetKey, Definitions

from swiss_ai_hub.backup.dagster.assets.backup_finalize_factory import backup_finalize_factory
from swiss_ai_hub.backup.dagster.assets.backup_service_factory import backup_service_factory
from swiss_ai_hub.backup.dagster.assets.backup_session_factory import backup_session_factory
from swiss_ai_hub.backup.dagster.assets.maintenance_finalize_factory import maintenance_finalize_factory
from swiss_ai_hub.backup.dagster.assets.maintenance_handler_factory import (
    CLEANUP_HANDLER_NAMES,
    REPACK_HANDLER_NAMES,
)
from swiss_ai_hub.backup.dagster.assets.maintenance_service_factory import maintenance_service_factory
from swiss_ai_hub.backup.dagster.assets.maintenance_session_factory import maintenance_session_factory
from swiss_ai_hub.backup.dagster.assets.restore_finalize_factory import restore_finalize_factory
from swiss_ai_hub.backup.dagster.assets.restore_service_factory import restore_service_factory
from swiss_ai_hub.backup.dagster.assets.restore_session_factory import restore_session_factory
from swiss_ai_hub.backup.dagster.jobs.factory import (
    backup_asset_job,
    cleanup_asset_job,
    repack_asset_job,
    restore_asset_job,
)
from swiss_ai_hub.backup.dagster.resources.factory import backup_resources
from swiss_ai_hub.backup.dagster.schedules.factory import (
    daily_backup_schedule,
    monthly_repack_schedule,
    weekly_cleanup_schedule,
)


def backup_definitions() -> Definitions:
    session_key = AssetKey(["backup", "session"])
    service_keys = {
        "PostgreSQL": AssetKey(["backup", "postgres"]),
        "Milvus": AssetKey(["backup", "milvus"]),
        "Neo4j": AssetKey(["backup", "neo4j"]),
        "ClickHouse": AssetKey(["backup", "clickhouse"]),
        "Valkey": AssetKey(["backup", "valkey"]),
        "NATS": AssetKey(["backup", "nats"]),
    }
    finalize_key = AssetKey(["backup", "finalize"])

    session = backup_session_factory(session_key)
    service_assets = [
        backup_service_factory(key, session_key, name, f"{name} backup") for name, key in service_keys.items()
    ]
    finalize = backup_finalize_factory(finalize_key, session_key, service_keys)
    backup_assets = [session, *service_assets, finalize]

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

    maintenance_session_key = AssetKey(["maintenance", "session"])
    cleanup_service_keys = {name: AssetKey(["maintenance", name]) for name in CLEANUP_HANDLER_NAMES}
    cleanup_finalize_key = AssetKey(["maintenance", "cleanup_finalize"])

    repack_service_keys = {name: AssetKey(["maintenance", name]) for name in REPACK_HANDLER_NAMES}
    repack_finalize_key = AssetKey(["maintenance", "repack_finalize"])

    maintenance_session_asset = maintenance_session_factory(maintenance_session_key)
    cleanup_service_assets = [
        maintenance_service_factory(key, maintenance_session_key, name, f"Maintenance: {name}")
        for name, key in cleanup_service_keys.items()
    ]
    cleanup_finalize = maintenance_finalize_factory(cleanup_finalize_key, maintenance_session_key, cleanup_service_keys)
    cleanup_assets = [maintenance_session_asset, *cleanup_service_assets, cleanup_finalize]

    repack_service_assets = [
        maintenance_service_factory(key, maintenance_session_key, name, f"Maintenance: {name}")
        for name, key in repack_service_keys.items()
    ]
    repack_finalize = maintenance_finalize_factory(repack_finalize_key, maintenance_session_key, repack_service_keys)
    # The repack job materializes maintenance_session, the repack handler(s), and its own finalize.
    # cleanup and repack share the same session asset definition but are selected as separate jobs.
    repack_assets = [*repack_service_assets, repack_finalize]

    backup_job = backup_asset_job(backup_assets)
    restore_job = restore_asset_job(restore_assets)
    cleanup_job = cleanup_asset_job([maintenance_session_asset, *cleanup_service_assets, cleanup_finalize])
    repack_job = repack_asset_job([maintenance_session_asset, *repack_service_assets, repack_finalize])

    schedule = daily_backup_schedule(backup_job)
    cleanup_schedule = weekly_cleanup_schedule(cleanup_job)
    repack_schedule = monthly_repack_schedule(repack_job)

    resources = backup_resources()

    return Definitions(
        assets=[*backup_assets, *restore_assets, *cleanup_assets, *repack_assets],
        jobs=[backup_job, restore_job, cleanup_job, repack_job],
        schedules=[schedule, cleanup_schedule, repack_schedule],
        resources=resources,
    )
