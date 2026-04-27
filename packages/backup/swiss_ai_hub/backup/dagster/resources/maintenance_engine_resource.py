from dagster import ConfigurableResource, InitResourceContext
from sqlalchemy import Engine

from swiss_ai_hub.backup.dagster.resources.backup_settings_resource import BackupSettingsResource
from swiss_ai_hub.backup.maintenance.postgres_engine import build_dagster_engine


class MaintenanceEngineResource(ConfigurableResource[Engine]):
    """Yields a SQLAlchemy ``Engine`` for the dagster Postgres database.

    Constructed lazily inside ``create_resource`` so the engine is only built
    when an asset that needs it actually executes (the backup-only daily run
    does not).
    """

    settings: BackupSettingsResource

    def create_resource(self, context: InitResourceContext) -> Engine:
        return build_dagster_engine(self.settings.create_resource(context))
