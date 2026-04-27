from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import NullPool

from swiss_ai_hub.backup.settings import BackupSettings


def build_dagster_engine(settings: BackupSettings) -> Engine:
    """Build a SQLAlchemy engine for the dagster Postgres database.

    Uses NullPool because maintenance runs are infrequent and short-lived;
    pooling adds zero value and complicates connection state across runs.
    Connects directly to postgres rather than pgbouncer because the maintenance
    workload (long-running DELETEs, CREATE INDEX CONCURRENTLY, ALTER TABLE)
    benefits from a stable session-mode connection.
    """
    url = (
        f"postgresql+psycopg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD.get_secret_value()}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}"
        f"/{settings.DAGSTER_DB}"
    )
    return create_engine(url, poolclass=NullPool, connect_args={"application_name": "swiss-ai-hub-maintenance"})
