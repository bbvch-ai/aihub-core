from collections.abc import Generator

from dagster import ConfigurableResource, InitResourceContext
from sqlalchemy import Engine

from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.maintenance.postgres_engine import build_dagster_engine


class MaintenanceEngineResource(ConfigurableResource[Engine]):
    """Yields a SQLAlchemy ``Engine`` for the dagster Postgres database.

    Constructed lazily inside ``yield_for_execution`` so the engine is only
    built when an asset that needs it actually executes (the backup-only
    daily run does not). Disposed on teardown to release any lingering
    connection state and silence SQLAlchemy "Engine not disposed" warnings.
    """

    settings: BackupSettingsResource

    def yield_for_execution(self, context: InitResourceContext) -> Generator[Engine]:
        engine = build_dagster_engine(self.settings.create_resource(context))
        try:
            yield engine
        finally:
            engine.dispose()
