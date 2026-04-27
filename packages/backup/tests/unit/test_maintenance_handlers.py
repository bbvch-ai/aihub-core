"""Unit tests for the maintenance handlers (no Postgres required — engine is mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.maintenance.dagster_unimportant_events import (
    _UNIMPORTANT_EVENT_TYPES,
    DagsterUnimportantEventsHandler,
)
from swiss_ai_hub.backup.maintenance.log_level_cleanup_handler import LogLevelCleanupHandler
from swiss_ai_hub.backup.maintenance.postgres_autovacuum_tune import PostgresAutovacuumTuneHandler
from swiss_ai_hub.backup.maintenance.postgres_indexes import PostgresIndexesHandler
from swiss_ai_hub.backup.maintenance.postgres_repack import PostgresRepackHandler


def _debug_handler(engine: MagicMock | object, retention: int = 7, limit: int = 1_000_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_debug_logs", "10", engine, retention, limit)


def _info_handler(engine: MagicMock | object, retention: int = 60, limit: int = 1_000_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_info_logs", "20", engine, retention, limit)


def _warning_handler(engine: MagicMock | object, retention: int = 60, limit: int = 1_000_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_warning_logs", "30", engine, retention, limit)


def _mock_engine_with_rowcount(rowcount: int) -> MagicMock:
    engine = MagicMock()
    cm = engine.begin.return_value.__enter__.return_value
    result = MagicMock()
    result.rowcount = rowcount
    cm.execute.return_value = result
    return engine


def _captured_delete_sql(engine: MagicMock) -> str:
    """Return the DELETE SQL passed to conn.execute() — for WHERE-clause assertions."""
    cm = engine.begin.return_value.__enter__.return_value
    for call in cm.execute.call_args_list:
        text_obj = call.args[0]
        sql = str(getattr(text_obj, "text", text_obj))
        if "DELETE FROM event_logs" in sql:
            return sql
    raise AssertionError("No DELETE FROM event_logs SQL was issued")


@pytest.mark.unit
@pytest.mark.parametrize("handler_factory", [_debug_handler, _info_handler, _warning_handler])
def test_log_cleanup_handlers_return_rows_deleted(handler_factory) -> None:
    engine = _mock_engine_with_rowcount(42)
    handler = handler_factory(engine)
    result = handler.run()
    assert result.succeeded
    assert result.rows_affected == 42
    assert result.error is None


@pytest.mark.unit
def test_unimportant_events_handler_targets_curated_event_types() -> None:
    """Spot-check that the WHERE clause references the documented event types."""
    expected = {"ASSET_MATERIALIZATION_PLANNED", "ENGINE_EVENT", "HANDLED_OUTPUT", "LOADED_INPUT", "STEP_OUTPUT"}
    assert set(_UNIMPORTANT_EVENT_TYPES) == expected


@pytest.mark.unit
def test_unimportant_events_handler_excludes_asset_materialization() -> None:
    """ASSET_MATERIALIZATION must NEVER be deleted — the asset catalog depends on it."""
    assert "ASSET_MATERIALIZATION" not in _UNIMPORTANT_EVENT_TYPES
    assert "STEP_SUCCESS" not in _UNIMPORTANT_EVENT_TYPES
    assert "STEP_FAILURE" not in _UNIMPORTANT_EVENT_TYPES


@pytest.mark.unit
def test_log_cleanup_handler_returns_failure_on_db_error() -> None:
    engine = MagicMock()
    engine.begin.return_value.__enter__.side_effect = RuntimeError("connection refused")
    handler = _debug_handler(engine)
    result = handler.run()
    assert not result.succeeded
    assert "connection refused" in (result.error or "")


@pytest.mark.unit
def test_unimportant_events_handler_passes_through_rowcount() -> None:
    engine = _mock_engine_with_rowcount(123_456)
    handler = DagsterUnimportantEventsHandler(engine, delete_after_days=30, batch_limit=1_000_000)
    result = handler.run()
    assert result.succeeded
    assert result.rows_affected == 123_456


@pytest.mark.unit
def test_postgres_indexes_handler_runs_create_index_concurrently() -> None:
    engine = MagicMock()
    conn = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    conn.execute.return_value.first.return_value = None  # no existing index
    handler = PostgresIndexesHandler(engine)
    result = handler.run()
    assert result.succeeded
    # AUTOCOMMIT isolation is required for CREATE INDEX CONCURRENTLY
    engine.connect.return_value.execution_options.assert_called_with(isolation_level="AUTOCOMMIT")


@pytest.mark.unit
def test_postgres_indexes_handler_is_idempotent_when_indexes_exist() -> None:
    engine = MagicMock()
    conn = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    conn.execute.return_value.first.return_value = (1,)  # index already exists
    handler = PostgresIndexesHandler(engine)
    result = handler.run()
    assert result.succeeded
    assert "none (already present)" in result.metadata.get("indexes_created", "")


@pytest.mark.unit
def test_autovacuum_tune_skips_missing_tables() -> None:
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    conn.execute.return_value.all.return_value = [("event_logs",)]  # only event_logs exists
    handler = PostgresAutovacuumTuneHandler(engine)
    result = handler.run()
    assert result.succeeded
    tables = result.metadata.get("tables_tuned", "")
    assert "event_logs" in tables
    assert "runs" not in tables


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_skips_when_binary_missing(mock_which: MagicMock) -> None:
    mock_which.return_value = None
    settings = MagicMock()
    handler = PostgresRepackHandler(settings)
    result = handler.run()
    assert result.succeeded
    assert "skipped" in result.metadata


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_runs_for_each_table_when_binary_present(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
    settings = MagicMock()
    settings.POSTGRES_PASSWORD.get_secret_value.return_value = "secret"
    settings.MAINTENANCE_POSTGRES_HOST = "postgres"
    settings.MAINTENANCE_POSTGRES_PORT = 5432
    settings.POSTGRES_USER = "admin"
    settings.MAINTENANCE_DAGSTER_DB = "dagster"
    handler = PostgresRepackHandler(settings)
    result = handler.run()
    assert result.succeeded
    assert mock_subprocess.call_count == 3  # event_logs, runs, job_ticks


# ---------------------------------------------------------------------------
# Handler-specific WHERE clause assertions — these match the official
# docs.dagster.io/deployment/troubleshooting/database-tuning recipe exactly.
# Drift here = potential UI breakage.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_debug_logs_handler_targets_level_10_user_logs_only() -> None:
    engine = _mock_engine_with_rowcount(0)
    _debug_handler(engine, retention=7, limit=100).run()
    sql = _captured_delete_sql(engine)
    assert "dagster_event_type IS NULL" in sql
    assert "event::jsonb->>'level' = '10'" in sql


@pytest.mark.unit
def test_info_logs_handler_targets_level_20_user_logs_only() -> None:
    engine = _mock_engine_with_rowcount(0)
    _info_handler(engine, retention=60, limit=100).run()
    sql = _captured_delete_sql(engine)
    assert "dagster_event_type IS NULL" in sql
    assert "event::jsonb->>'level' = '20'" in sql


@pytest.mark.unit
def test_warning_logs_handler_targets_level_30_user_logs_only() -> None:
    engine = _mock_engine_with_rowcount(0)
    _warning_handler(engine, retention=60, limit=100).run()
    sql = _captured_delete_sql(engine)
    assert "dagster_event_type IS NULL" in sql
    assert "event::jsonb->>'level' = '30'" in sql


@pytest.mark.unit
def test_unimportant_events_handler_targets_documented_event_types() -> None:
    engine = _mock_engine_with_rowcount(0)
    DagsterUnimportantEventsHandler(engine, 30, 100).run()
    sql = _captured_delete_sql(engine)
    for event_type in (
        "ASSET_MATERIALIZATION_PLANNED",
        "ENGINE_EVENT",
        "HANDLED_OUTPUT",
        "LOADED_INPUT",
        "STEP_OUTPUT",
    ):
        assert event_type in sql
    # Critical: the asset catalog and run detail page depend on these — must NEVER appear.
    assert "ASSET_MATERIALIZATION'" not in sql.replace("ASSET_MATERIALIZATION_PLANNED", "")
    assert "STEP_SUCCESS" not in sql
    assert "STEP_FAILURE" not in sql


@pytest.mark.unit
@pytest.mark.parametrize(
    ("handler_factory", "after_days", "limit"),
    [
        (_debug_handler, 14, 500_000),
        (_info_handler, 90, 250_000),
        (_warning_handler, 30, 100_000),
    ],
)
def test_log_handlers_pass_configured_retention_and_limit(handler_factory, after_days: int, limit: int) -> None:
    engine = _mock_engine_with_rowcount(0)
    handler_factory(engine, retention=after_days, limit=limit).run()
    cm = engine.begin.return_value.__enter__.return_value
    delete_call = next(c for c in cm.execute.call_args_list if "DELETE FROM event_logs" in str(c.args[0]))
    params = delete_call.args[1]
    assert params == {"delete_after_days": after_days, "batch_limit": limit}


@pytest.mark.unit
def test_unimportant_events_handler_passes_configured_retention_and_limit() -> None:
    engine = _mock_engine_with_rowcount(0)
    DagsterUnimportantEventsHandler(engine, 7, 1_000).run()
    cm = engine.begin.return_value.__enter__.return_value
    delete_call = next(c for c in cm.execute.call_args_list if "DELETE FROM event_logs" in str(c.args[0]))
    params = delete_call.args[1]
    assert params == {"delete_after_days": 7, "batch_limit": 1_000}


@pytest.mark.unit
def test_log_handler_metadata_includes_retention_limit_and_level() -> None:
    engine = _mock_engine_with_rowcount(99)
    result = _debug_handler(engine, retention=14, limit=500_000).run()
    assert result.metadata["retention_days"] == 14
    assert result.metadata["batch_limit"] == 500_000
    assert result.metadata["level"] == "10"


@pytest.mark.unit
def test_indexes_handler_creates_both_documented_indexes() -> None:
    engine = MagicMock()
    conn = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    conn.execute.return_value.first.return_value = None
    PostgresIndexesHandler(engine).run()
    issued_ddl = [str(c.args[0].text) for c in conn.execute.call_args_list]
    assert any("idx_clear_event_logs_user_logs" in s for s in issued_ddl)
    assert any("idx_clear_event_logs_system_events" in s for s in issued_ddl)
    assert all("CONCURRENTLY" in s for s in issued_ddl if "CREATE INDEX" in s)
    assert all("IF NOT EXISTS" in s for s in issued_ddl if "CREATE INDEX" in s)


@pytest.mark.unit
def test_indexes_handler_records_only_actually_created_indexes() -> None:
    """If one index exists and the other doesn't, metadata reports only the new one."""
    engine = MagicMock()
    conn = engine.connect.return_value.execution_options.return_value.__enter__.return_value
    # First check: existing. Second check: missing.
    conn.execute.return_value.first.side_effect = [(1,), None]
    result = PostgresIndexesHandler(engine).run()
    assert result.succeeded
    assert "idx_clear_event_logs_system_events" in result.metadata.get("indexes_created", "")
    assert "idx_clear_event_logs_user_logs" not in result.metadata.get("indexes_created", "")


@pytest.mark.unit
def test_autovacuum_handler_emits_alter_table_with_documented_options() -> None:
    engine = MagicMock()
    conn = engine.begin.return_value.__enter__.return_value
    conn.execute.return_value.all.return_value = [("event_logs",), ("runs",)]
    PostgresAutovacuumTuneHandler(engine).run()
    issued = [str(c.args[0].text) for c in conn.execute.call_args_list if hasattr(c.args[0], "text")]
    event_logs_alter = next(s for s in issued if "ALTER TABLE event_logs" in s)
    assert "autovacuum_vacuum_scale_factor = 0.05" in event_logs_alter
    assert "autovacuum_analyze_scale_factor = 0.02" in event_logs_alter
    runs_alter = next(s for s in issued if "ALTER TABLE runs" in s)
    assert "autovacuum_vacuum_scale_factor = 0.10" in runs_alter


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_returns_skipped_when_extension_missing(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """If pg_repack binary is present but server-side extension is not, handler
    skips per-table rather than failing — operators may roll out the extension
    after the handler is deployed."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.CalledProcessError(
        returncode=1, cmd="pg_repack", stderr="pg_repack: ERROR: extension does not exist"
    )
    settings = MagicMock()
    settings.POSTGRES_PASSWORD.get_secret_value.return_value = "secret"
    settings.MAINTENANCE_POSTGRES_HOST = "postgres"
    settings.MAINTENANCE_POSTGRES_PORT = 5432
    settings.POSTGRES_USER = "admin"
    settings.MAINTENANCE_DAGSTER_DB = "dagster"
    result = PostgresRepackHandler(settings).run()
    assert result.succeeded
    skipped = result.metadata.get("skipped", "")
    assert "event_logs" in skipped or "no extension" in skipped


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_returns_failure_on_unexpected_error(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """An error that isn't 'extension missing' should fail the handler."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.CalledProcessError(
        returncode=1, cmd="pg_repack", stderr="pg_repack: ERROR: relation event_logs does not have a primary key"
    )
    settings = _mock_repack_settings()
    result = PostgresRepackHandler(settings).run()
    assert not result.succeeded
    assert "primary key" in (result.error or "")


def _mock_repack_settings() -> MagicMock:
    settings = MagicMock()
    settings.POSTGRES_PASSWORD.get_secret_value.return_value = "secret"
    settings.MAINTENANCE_POSTGRES_HOST = "postgres"
    settings.MAINTENANCE_POSTGRES_PORT = 5432
    settings.POSTGRES_USER = "admin"
    settings.MAINTENANCE_DAGSTER_DB = "dagster"
    return settings


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_fails_loudly_on_missing_table(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """A 'relation does not exist' error is NOT the missing-extension case —
    classify as failure rather than silent skip. Regression guard against the
    earlier ``or "does not exist"`` heuristic."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.CalledProcessError(
        returncode=1, cmd="pg_repack", stderr='pg_repack: ERROR: relation "event_logs" does not exist'
    )
    settings = _mock_repack_settings()
    result = PostgresRepackHandler(settings).run()
    assert not result.succeeded
    assert "does not exist" in (result.error or "")


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_fails_loudly_on_missing_column(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """A 'column does not exist' error is NOT the missing-extension case."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.CalledProcessError(
        returncode=1, cmd="pg_repack", stderr='pg_repack: ERROR: column "ctid" does not exist'
    )
    settings = _mock_repack_settings()
    result = PostgresRepackHandler(settings).run()
    assert not result.succeeded
    assert "column" in (result.error or "")


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_skips_on_explicit_not_installed_message(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """The wording pg_repack actually uses for the missing-extension case."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.CalledProcessError(
        returncode=1, cmd="pg_repack", stderr='pg_repack: ERROR: pg_repack is not installed in the database "dagster"'
    )
    settings = _mock_repack_settings()
    result = PostgresRepackHandler(settings).run()
    assert result.succeeded
    skipped = result.metadata.get("skipped", "")
    assert "no extension" in skipped


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_returns_failure_on_timeout(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """subprocess.TimeoutExpired must be caught — the per-handler failure-isolation
    contract requires returning MaintenanceResult, not raising."""
    import subprocess as sp

    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.side_effect = sp.TimeoutExpired(cmd="pg_repack", timeout=7200)
    settings = _mock_repack_settings()
    result = PostgresRepackHandler(settings).run()
    assert not result.succeeded
    assert "timed out" in (result.error or "")


@pytest.mark.unit
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.subprocess.run")
@patch("swiss_ai_hub.backup.maintenance.postgres_repack.shutil.which")
def test_postgres_repack_handler_sets_pgappname_for_pg_stat_activity(
    mock_which: MagicMock,
    mock_subprocess: MagicMock,
) -> None:
    """PGAPPNAME parity with the SQLAlchemy application_name lets DBAs see
    consistent labels in pg_stat_activity."""
    mock_which.return_value = "/usr/bin/pg_repack"
    mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
    settings = _mock_repack_settings()
    PostgresRepackHandler(settings).run()
    env = mock_subprocess.call_args.kwargs["env"]
    assert env["PGAPPNAME"] == "swiss-ai-hub-maintenance"
