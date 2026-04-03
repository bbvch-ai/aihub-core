from dagster import AssetKey, Definitions

from swiss_ai_hub.backup.dagster.assets.backup_finalize_factory import backup_finalize_factory
from swiss_ai_hub.backup.dagster.assets.backup_session_factory import backup_session_factory
from swiss_ai_hub.backup.dagster.jobs.factory import backup_asset_job
from swiss_ai_hub.backup.dagster.resources.container_discovery_resource import ContainerDiscoveryResource


def backup_definitions() -> Definitions:
    session_key = AssetKey(["backup", "session"])
    finalize_key = AssetKey(["backup", "finalize"])

    session = backup_session_factory(session_key)
    finalize = backup_finalize_factory(finalize_key, session_key)
    backup_assets = [session, finalize]

    job = backup_asset_job(backup_assets)

    resources: dict[str, object] = {
        "container_discovery": ContainerDiscoveryResource(),
    }

    return Definitions(
        assets=backup_assets,
        jobs=[job],
        resources=resources,
    )
