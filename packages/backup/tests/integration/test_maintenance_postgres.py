"""Layer 2 — SQL contract tests against a real Postgres.

These tests verify the SEMANTIC contract of the maintenance handlers:
  - Cleanup handlers preserve ASSET_MATERIALIZATION / STEP_SUCCESS / STEP_FAILURE
  - Cleanup handlers respect retention windows
  - Cleanup handlers respect batch_limit
  - Indexes handler creates the documented indexes
  - Autovacuum handler applies documented reloptions
  - Cleanup handlers DO NOT touch the runs / asset_keys tables

These run against a temp Postgres started by pytest-postgresql. They skip
automatically when ``pg_ctl`` is not on PATH.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Engine, text

from swiss_ai_hub.backup.maintenance.dagster_unimportant_events import DagsterUnimportantEventsHandler
from swiss_ai_hub.backup.maintenance.log_level_cleanup_handler import LogLevelCleanupHandler
from swiss_ai_hub.backup.maintenance.postgres_autovacuum_tune import PostgresAutovacuumTuneHandler
from swiss_ai_hub.backup.maintenance.postgres_indexes import PostgresIndexesHandler

from .conftest import count_rows


def _debug(engine, retention=7, limit=10_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_debug_logs", "10", engine, retention, limit)


def _info(engine, retention=60, limit=10_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_info_logs", "20", engine, retention, limit)


def _warning(engine, retention=60, limit=10_000) -> LogLevelCleanupHandler:
    return LogLevelCleanupHandler("dagster_warning_logs", "30", engine, retention, limit)


pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Cleanup handler semantics
# ---------------------------------------------------------------------------


def test_debug_logs_handler_deletes_only_old_level_10_user_logs(event_logs_engine: Engine, seed_events) -> None:
    seed_events(age_days=10, level="10")  # old DEBUG → should delete
    seed_events(age_days=2, level="10")  # young DEBUG → keep
    seed_events(age_days=10, level="20")  # old INFO → keep (different handler)
    seed_events(age_days=10, dagster_event_type="ASSET_MATERIALIZATION")  # framework event → keep
    seed_events(age_days=10, dagster_event_type="ENGINE_EVENT")  # framework event → keep

    result = _debug(event_logs_engine, retention=7, limit=10_000).run()
    assert result.succeeded
    assert result.rows_affected == 1
    # Only the old DEBUG was deleted; everything else preserved.
    assert count_rows(event_logs_engine) == 4


def test_info_logs_handler_deletes_only_old_level_20_user_logs(event_logs_engine: Engine, seed_events) -> None:
    seed_events(age_days=70, level="20")  # old INFO
    seed_events(age_days=10, level="20")  # young INFO
    seed_events(age_days=70, level="10")  # old DEBUG → keep (different handler)
    seed_events(age_days=70, level="30")  # old WARNING → keep (different handler)

    result = _info(event_logs_engine, retention=60, limit=10_000).run()
    assert result.succeeded
    assert result.rows_affected == 1
    assert count_rows(event_logs_engine) == 3


def test_warning_logs_handler_deletes_only_old_level_30_user_logs(event_logs_engine: Engine, seed_events) -> None:
    seed_events(age_days=70, level="30")
    seed_events(age_days=10, level="30")
    seed_events(age_days=70, level="20")

    result = _warning(event_logs_engine, retention=60, limit=10_000).run()
    assert result.succeeded
    assert result.rows_affected == 1
    assert count_rows(event_logs_engine) == 2


def test_unimportant_events_handler_deletes_documented_event_types(event_logs_engine: Engine, seed_events) -> None:
    """The most important assertion in the suite: ASSET_MATERIALIZATION etc. are preserved."""
    # Should be deleted:
    for et in ("ASSET_MATERIALIZATION_PLANNED", "ENGINE_EVENT", "HANDLED_OUTPUT", "LOADED_INPUT", "STEP_OUTPUT"):
        seed_events(age_days=40, dagster_event_type=et)
    # Must be preserved (UI relies on these):
    for et in ("ASSET_MATERIALIZATION", "STEP_SUCCESS", "STEP_FAILURE", "RUN_SUCCESS", "RUN_FAILURE"):
        seed_events(age_days=40, dagster_event_type=et)

    result = DagsterUnimportantEventsHandler(event_logs_engine, delete_after_days=30, batch_limit=10_000).run()
    assert result.succeeded
    assert result.rows_affected == 5  # the five documented unimportant types

    with event_logs_engine.connect() as conn:
        remaining = {row[0] for row in conn.execute(text("SELECT DISTINCT dagster_event_type FROM event_logs")).all()}
    assert remaining == {"ASSET_MATERIALIZATION", "STEP_SUCCESS", "STEP_FAILURE", "RUN_SUCCESS", "RUN_FAILURE"}


def test_unimportant_events_handler_preserves_recent_rows(event_logs_engine: Engine, seed_events) -> None:
    seed_events(age_days=10, dagster_event_type="ENGINE_EVENT")  # too new to delete
    seed_events(age_days=40, dagster_event_type="ENGINE_EVENT")  # old enough

    result = DagsterUnimportantEventsHandler(event_logs_engine, delete_after_days=30, batch_limit=10_000).run()
    assert result.succeeded
    assert result.rows_affected == 1
    assert count_rows(event_logs_engine) == 1


def test_cleanup_handler_is_idempotent(event_logs_engine: Engine, seed_events) -> None:
    seed_events(age_days=40, dagster_event_type="ENGINE_EVENT")

    h = DagsterUnimportantEventsHandler(event_logs_engine, delete_after_days=30, batch_limit=10_000)
    first = h.run()
    second = h.run()
    assert first.succeeded and first.rows_affected == 1
    assert second.succeeded and second.rows_affected == 0  # nothing left to delete


def test_cleanup_handler_respects_batch_limit(event_logs_engine: Engine, seed_events) -> None:
    """First call deletes batch_limit rows; subsequent calls drain the rest."""
    for _ in range(25):
        seed_events(age_days=40, dagster_event_type="ENGINE_EVENT")

    h = DagsterUnimportantEventsHandler(event_logs_engine, delete_after_days=30, batch_limit=10)
    first = h.run()
    assert first.rows_affected == 10
    assert count_rows(event_logs_engine) == 15

    second = h.run()
    assert second.rows_affected == 10
    assert count_rows(event_logs_engine) == 5

    third = h.run()
    assert third.rows_affected == 5
    assert count_rows(event_logs_engine) == 0


def test_cleanup_handlers_run_together_preserve_user_visible_data(event_logs_engine: Engine, seed_events) -> None:
    """Composition test: run all four cleanup handlers, asset materializations stay."""
    # Old data that should ALL be deleted:
    seed_events(age_days=30, level="10")  # debug
    seed_events(age_days=70, level="20")  # info
    seed_events(age_days=70, level="30")  # warning
    seed_events(age_days=40, dagster_event_type="HANDLED_OUTPUT")
    seed_events(age_days=40, dagster_event_type="LOADED_INPUT")

    # Old data that MUST stay (asset catalog / run detail UI depends on it):
    seed_events(age_days=200, dagster_event_type="ASSET_MATERIALIZATION", asset_key="my_asset")
    seed_events(age_days=200, dagster_event_type="STEP_SUCCESS")
    seed_events(age_days=200, dagster_event_type="STEP_FAILURE")
    seed_events(age_days=200, dagster_event_type="RUN_SUCCESS")

    _debug(event_logs_engine, 7, 10_000).run()
    _info(event_logs_engine, 60, 10_000).run()
    _warning(event_logs_engine, 60, 10_000).run()
    DagsterUnimportantEventsHandler(event_logs_engine, 30, 10_000).run()

    with event_logs_engine.connect() as conn:
        remaining = {
            row[0]
            for row in conn.execute(text("SELECT DISTINCT dagster_event_type FROM event_logs")).all()
            if row[0] is not None
        }
    assert remaining == {"ASSET_MATERIALIZATION", "STEP_SUCCESS", "STEP_FAILURE", "RUN_SUCCESS"}
    assert count_rows(event_logs_engine) == 4


def test_cleanup_handlers_do_not_touch_runs_table(event_logs_engine: Engine, seed_events) -> None:
    """The Runs tab in the Dagster UI depends on rows in the runs table."""
    with event_logs_engine.begin() as conn:
        for i in range(5):
            conn.execute(
                text(
                    "INSERT INTO runs (run_id, status, create_timestamp) "
                    "VALUES (:rid, 'SUCCESS', CURRENT_DATE - MAKE_INTERVAL(days => :age))"
                ),
                {"rid": f"old_run_{i}", "age": 200},
            )

    seed_events(age_days=40, dagster_event_type="ENGINE_EVENT")
    DagsterUnimportantEventsHandler(event_logs_engine, 30, 10_000).run()

    with event_logs_engine.connect() as conn:
        runs_count = conn.execute(text("SELECT COUNT(*) FROM runs")).scalar()
    assert runs_count == 5  # untouched


def test_cleanup_handlers_do_not_touch_asset_keys_table(event_logs_engine: Engine, seed_events) -> None:
    """The asset catalog UI depends on asset_keys."""
    with event_logs_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO asset_keys (asset_key, last_materialization_timestamp) "
                "VALUES ('my_asset', CURRENT_DATE - MAKE_INTERVAL(days => 200))"
            )
        )

    seed_events(age_days=40, dagster_event_type="ENGINE_EVENT")
    DagsterUnimportantEventsHandler(event_logs_engine, 30, 10_000).run()

    with event_logs_engine.connect() as conn:
        ak_count = conn.execute(text("SELECT COUNT(*) FROM asset_keys")).scalar()
    assert ak_count == 1


# ---------------------------------------------------------------------------
# Indexes handler
# ---------------------------------------------------------------------------


def test_indexes_handler_creates_both_documented_indexes(event_logs_engine: Engine) -> None:
    PostgresIndexesHandler(event_logs_engine).run()
    with event_logs_engine.connect() as conn:
        indexes = {
            row[0]
            for row in conn.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'event_logs'")).all()
        }
    assert "idx_clear_event_logs_user_logs" in indexes
    assert "idx_clear_event_logs_system_events" in indexes


def test_indexes_handler_is_idempotent(event_logs_engine: Engine) -> None:
    h = PostgresIndexesHandler(event_logs_engine)
    h.run()
    second = h.run()
    assert second.succeeded
    assert second.metadata.get("indexes_created") == "none (already present)"


def test_indexes_handler_creates_only_missing_indexes(event_logs_engine: Engine) -> None:
    """Pre-create one index manually; the handler should add only the other."""
    with event_logs_engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX idx_clear_event_logs_user_logs "
                "ON event_logs ((event::jsonb ->> 'level'::text), timestamp) "
                "WHERE (dagster_event_type IS NULL)"
            )
        )

    result = PostgresIndexesHandler(event_logs_engine).run()
    assert result.succeeded
    created = result.metadata.get("indexes_created", "")
    assert "idx_clear_event_logs_system_events" in created
    assert "idx_clear_event_logs_user_logs" not in created


# ---------------------------------------------------------------------------
# Autovacuum tune handler
# ---------------------------------------------------------------------------


def test_autovacuum_tune_applies_reloptions_to_event_logs(event_logs_engine: Engine) -> None:
    PostgresAutovacuumTuneHandler(event_logs_engine).run()
    with event_logs_engine.connect() as conn:
        reloptions = conn.execute(text("SELECT reloptions FROM pg_class WHERE relname = 'event_logs'")).scalar()
    assert reloptions is not None
    joined = ",".join(reloptions)
    assert "autovacuum_vacuum_scale_factor=0.05" in joined
    assert "autovacuum_analyze_scale_factor=0.02" in joined


def test_autovacuum_tune_applies_reloptions_to_runs(event_logs_engine: Engine) -> None:
    PostgresAutovacuumTuneHandler(event_logs_engine).run()
    with event_logs_engine.connect() as conn:
        reloptions = conn.execute(text("SELECT reloptions FROM pg_class WHERE relname = 'runs'")).scalar()
    assert reloptions is not None
    assert any("autovacuum_vacuum_scale_factor=0.10" in opt for opt in reloptions)


def test_autovacuum_tune_skips_missing_tables(event_logs_engine: Engine) -> None:
    """If a target table doesn't exist (e.g., fresh DB before Dagster migrate),
    the handler should report which tables WERE tuned and not error."""
    with event_logs_engine.begin() as conn:
        conn.execute(text("DROP TABLE runs"))

    result = PostgresAutovacuumTuneHandler(event_logs_engine).run()
    assert result.succeeded
    tables = result.metadata.get("tables_tuned", "")
    assert "event_logs" in tables
    assert "runs" not in tables


def test_autovacuum_tune_is_idempotent(event_logs_engine: Engine) -> None:
    h = PostgresAutovacuumTuneHandler(event_logs_engine)
    h.run()
    second = h.run()
    assert second.succeeded
