from dagster import AssetExecutionContext, Definitions, asset


@asset(key=["backup", "healthcheck"])
def backup_healthcheck(context: AssetExecutionContext) -> None:
    """Placeholder asset to verify the backup Dagster service is running."""
    context.log.info("Backup service is running")


def backup_definitions() -> Definitions:
    return Definitions(
        assets=[backup_healthcheck],
    )
