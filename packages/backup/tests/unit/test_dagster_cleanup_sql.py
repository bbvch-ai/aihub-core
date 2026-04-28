"""Unit tests for the shared SQL helper used by all four cleanup handlers.

These tests verify the *shape* of the SQL: that LIMIT is applied via CTE,
parameters are passed correctly, statement_timeout is set, and rowcount is
returned. The actual semantics (does this SQL preserve ASSET_MATERIALIZATION?)
are tested in the Layer 2 integration tests against real Postgres.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.backup.maintenance.dagster_cleanup_sql import execute_capped_delete


def _captured_sql_calls(engine: MagicMock) -> list[tuple[str, dict]]:
    """Extract (sql, params) tuples from all conn.execute() calls."""
    cm = engine.begin.return_value.__enter__.return_value
    calls = []
    for call in cm.execute.call_args_list:
        text_obj = call.args[0]
        sql = str(getattr(text_obj, "text", text_obj))
        params = call.args[1] if len(call.args) > 1 else {}
        calls.append((sql, params))
    return calls


def _engine_with_rowcount(rowcount: int) -> MagicMock:
    engine = MagicMock()
    cm = engine.begin.return_value.__enter__.return_value
    cm.execute.return_value = MagicMock(rowcount=rowcount)
    return engine


@pytest.mark.unit
def test_execute_capped_delete_returns_rowcount_and_duration() -> None:
    engine = _engine_with_rowcount(100)
    rows, duration = execute_capped_delete(engine, "lbl", "1=1", 7, 1000)
    assert rows == 100
    assert duration >= 0.0


@pytest.mark.unit
def test_execute_capped_delete_uses_cte_with_limit() -> None:
    """Standard PostgreSQL DELETE doesn't support LIMIT — must use a CTE."""
    engine = _engine_with_rowcount(0)
    execute_capped_delete(engine, "lbl", "dagster_event_type IS NULL", 7, 1_000_000)
    calls = _captured_sql_calls(engine)
    delete_sql = next(sql for sql, _ in calls if "DELETE FROM event_logs" in sql)
    assert "WITH targets AS" in delete_sql
    assert "LIMIT :batch_limit" in delete_sql
    assert "WHERE id IN (SELECT id FROM targets)" in delete_sql


@pytest.mark.unit
def test_execute_capped_delete_passes_parameters() -> None:
    engine = _engine_with_rowcount(0)
    execute_capped_delete(engine, "lbl", "1=1", 14, 500_000)
    calls = _captured_sql_calls(engine)
    delete_call = next(c for c in calls if "DELETE FROM event_logs" in c[0])
    params = delete_call[1]
    assert params == {"delete_after_days": 14, "batch_limit": 500_000}


@pytest.mark.unit
def test_execute_capped_delete_interpolates_where_clause_inline() -> None:
    """The where_clause is internal-only (not user input) so inline interpolation is safe.

    Verifying it's actually inlined catches the failure mode where someone
    accidentally tries to bind it as a parameter (which would silently change
    SQL semantics).
    """
    engine = _engine_with_rowcount(0)
    where = "dagster_event_type IN ('FOO', 'BAR') AND custom_col = 1"
    execute_capped_delete(engine, "lbl", where, 7, 100)
    calls = _captured_sql_calls(engine)
    delete_sql = next(sql for sql, _ in calls if "DELETE FROM event_logs" in sql)
    assert where in delete_sql


@pytest.mark.unit
def test_execute_capped_delete_sets_statement_timeout() -> None:
    """SET LOCAL statement_timeout protects against runaway queries."""
    engine = _engine_with_rowcount(0)
    execute_capped_delete(engine, "lbl", "1=1", 7, 100)
    calls = _captured_sql_calls(engine)
    assert any("SET LOCAL statement_timeout" in sql for sql, _ in calls)


@pytest.mark.unit
def test_execute_capped_delete_uses_make_interval() -> None:
    """The official Dagster docs use MAKE_INTERVAL — verify we match exactly so
    operators reading both sources see identical SQL."""
    engine = _engine_with_rowcount(0)
    execute_capped_delete(engine, "lbl", "1=1", 7, 100)
    calls = _captured_sql_calls(engine)
    delete_sql = next(sql for sql, _ in calls if "DELETE FROM event_logs" in sql)
    assert "CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)" in delete_sql
