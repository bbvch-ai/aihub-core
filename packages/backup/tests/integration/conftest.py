"""Shared fixtures for integration tests that need a real Postgres.

Uses ``pytest-postgresql`` in one of two modes:

  1. **Process mode** (default if ``pg_ctl`` is on PATH): spin up an ephemeral
     Postgres per session. Linux: ``apt install postgresql``.
  2. **Noproc mode**: connect to an existing Postgres reachable via
     ``PYTEST_POSTGRES_HOST`` + ``PYTEST_POSTGRES_PORT`` + ``PYTEST_POSTGRES_PASSWORD``.
     Useful in CI (postgres service container) or local dev (``docker run postgres``).

If neither is available, all integration tests skip with a clear message.

Run locally:
    # Option A: install postgres
    apt install postgresql && cd packages/backup && uv run pytest tests/integration/

    # Option B: docker postgres
    docker run --rm -d --name pg-test -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:17
    PYTEST_POSTGRES_HOST=localhost PYTEST_POSTGRES_PORT=55432 PYTEST_POSTGRES_PASSWORD=test \
        uv run pytest tests/integration/
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.pool import NullPool

PG_CTL_AVAILABLE = shutil.which("pg_ctl") is not None
EXTERNAL_PG_HOST = os.environ.get("PYTEST_POSTGRES_HOST")
EXTERNAL_PG_PORT = int(os.environ.get("PYTEST_POSTGRES_PORT", "5432")) if EXTERNAL_PG_HOST else None
EXTERNAL_PG_USER = os.environ.get("PYTEST_POSTGRES_USER", "postgres")
EXTERNAL_PG_PASSWORD = os.environ.get("PYTEST_POSTGRES_PASSWORD", "")


def _skip_without_postgres() -> None:
    if not PG_CTL_AVAILABLE and not EXTERNAL_PG_HOST:
        pytest.skip(
            "No Postgres available. Install pg_ctl or set PYTEST_POSTGRES_HOST.",
            allow_module_level=False,
        )


def _resolve_pg_bin_path() -> str | None:
    pg_ctl = shutil.which("pg_ctl")
    if pg_ctl is None:
        return None
    return os.path.dirname(pg_ctl)


if PG_CTL_AVAILABLE:
    from pytest_postgresql import factories  # noqa: PLC0415

    _PG_BIN = _resolve_pg_bin_path()
    postgresql_proc = factories.postgresql_proc(
        executable=os.path.join(_PG_BIN, "pg_ctl") if _PG_BIN else None,
        port=None,
    )
    postgresql_db = factories.postgresql("postgresql_proc", dbname="dagster_test")

elif EXTERNAL_PG_HOST:
    from pytest_postgresql import factories  # noqa: PLC0415

    postgresql_proc = factories.postgresql_noproc(
        host=EXTERNAL_PG_HOST,
        port=EXTERNAL_PG_PORT,
        user=EXTERNAL_PG_USER,
        password=EXTERNAL_PG_PASSWORD,
    )
    postgresql_db = factories.postgresql("postgresql_proc", dbname="dagster_test")

else:

    @pytest.fixture
    def postgresql_db() -> None:
        _skip_without_postgres()


@pytest.fixture
def event_logs_engine(postgresql_db) -> Iterator[Engine]:
    """SQLAlchemy engine pointed at the temp Postgres, with a minimal ``event_logs``
    schema matching the Dagster column names the cleanup SQL relies on.

    Schema is intentionally a SUBSET of Dagster's real schema — only the columns
    referenced by the cleanup queries (id, dagster_event_type, event jsonb,
    timestamp). Plus runs and asset_keys for negative assertions ("we don't
    touch these tables").
    """
    _skip_without_postgres()
    info = postgresql_db.info
    url = (
        f"postgresql+psycopg://{info.user}:{info.password}@{info.host}:{info.port}/{info.dbname}"
        if info.password
        else f"postgresql+psycopg://{info.user}@{info.host}:{info.port}/{info.dbname}"
    )
    engine = create_engine(url, poolclass=NullPool)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE event_logs (
                    id BIGSERIAL PRIMARY KEY,
                    run_id TEXT,
                    dagster_event_type TEXT,
                    event JSONB,
                    asset_key TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT,
                    create_timestamp TIMESTAMP WITH TIME ZONE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE asset_keys (
                    id BIGSERIAL PRIMARY KEY,
                    asset_key TEXT NOT NULL UNIQUE,
                    last_materialization_timestamp TIMESTAMP WITH TIME ZONE
                )
                """
            )
        )
    try:
        yield engine
    finally:
        engine.dispose()


def _seed_event(
    conn,
    *,
    age_days: int,
    dagster_event_type: str | None = None,
    level: str | None = None,
    asset_key: str | None = None,
) -> None:
    """Insert one event_logs row at ``CURRENT_DATE - age_days`` with given attrs."""
    event_payload = "{}" if level is None else f'{{"level": "{level}"}}'
    conn.execute(
        text(
            """
            INSERT INTO event_logs (run_id, dagster_event_type, event, asset_key, timestamp)
            VALUES (
                :run_id,
                :event_type,
                CAST(:event AS jsonb),
                :asset_key,
                CURRENT_DATE - MAKE_INTERVAL(days => :age)
            )
            """
        ),
        {
            "run_id": "run_1",
            "event_type": dagster_event_type,
            "event": event_payload,
            "asset_key": asset_key,
            "age": age_days,
        },
    )


@pytest.fixture
def seed_events(event_logs_engine: Engine):
    """Helper bound to the engine — usage: ``seed_events(age_days=10, level='10', ...)``."""

    def _seed(**kwargs) -> None:
        with event_logs_engine.begin() as conn:
            _seed_event(conn, **kwargs)

    return _seed


def count_rows(engine: Engine, where: str = "TRUE") -> int:
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM event_logs WHERE {where}")).scalar() or 0
