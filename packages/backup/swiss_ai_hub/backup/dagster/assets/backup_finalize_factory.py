from dagster import AssetExecutionContext, AssetIn, AssetKey, AssetsDefinition, ResourceParam, asset

from swiss_ai_hub.backup.container_discovery import ContainerDiscovery
from swiss_ai_hub.backup.dagster.ops.types import BackupContext


def backup_finalize_factory(
    key: AssetKey,
    session_key: AssetKey,
) -> AssetsDefinition:
    @asset(
        key=key,
        group_name="backup",
        ins={"session": AssetIn(key=session_key)},
        description="Restart all previously running containers",
    )
    def backup_finalize(
        context: AssetExecutionContext,
        session: BackupContext,
        container_discovery: ResourceParam[ContainerDiscovery],
    ) -> None:
        container_discovery.start_all(session.previously_running)

        context.add_output_metadata(
            {"containers_restarted": len(session.previously_running)},
        )

    return backup_finalize
