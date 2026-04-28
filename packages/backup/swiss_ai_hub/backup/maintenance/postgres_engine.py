from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.pool import NullPool

from swiss_ai_hub.backup.settings import BackupSettings


def build_dagster_engine(settings: BackupSettings) -> Engine:
    """Build a SQLAlchemy engine for the dagster Postgres database.

    Uses NullPool because maintenance runs are infrequent and short-lived;
    pooling adds zero value and complicates connection state across runs.
    Connects directly to postgres rather than pgbouncer because the maintenance
    workload (long-running DELETEs, CREATE INDEX CONCURRENTLY, ALTER TABLE)
    benefits from a stable session-mode connection.

    Uses ``URL.create()`` rather than f-string interpolation so passwords with
    URL-reserved characters (``@``, ``:``, ``/``, ``#``, ``?``) are escaped
    correctly. Hex-only secrets work either way; deployments using
    password-policy-style passwords (special chars) require this.
    """
    url = URL.create(
        drivername="postgresql+psycopg",
        username=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD.get_secret_value(),
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.DAGSTER_DB,
    )
    return create_engine(url, poolclass=NullPool, connect_args={"application_name": "swiss-ai-hub-maintenance"})
