"""Shared SQL execution helper for the four dagster_cleanup handlers.

Each handler issues one parameterized DELETE with a LIMIT cap (the docs use
unbounded DELETEs; we cap to avoid WAL spikes on backlogged DBs). The
LIMIT is applied via a CTE since standard PostgreSQL DELETE does not
support LIMIT directly.
"""

from __future__ import annotations

import logging
import time
from textwrap import dedent

from sqlalchemy import Engine, text

logger = logging.getLogger(__name__)

_TXN_TIMEOUT_SECONDS = 600


def execute_capped_delete(
    engine: Engine,
    label: str,
    where_clause: str,
    delete_after_days: int,
    batch_limit: int,
) -> tuple[int, float]:
    """Run a DELETE on ``event_logs`` filtered by ``where_clause``, capped at ``batch_limit`` rows.

    Returns ``(rows_deleted, duration_seconds)``. The caller is responsible
    for handling exceptions and writing them into the MaintenanceResult.
    The query uses CURRENT_DATE - MAKE_INTERVAL(...) to match the official
    Dagster recipe at docs.dagster.io/deployment/troubleshooting/database-tuning.
    """
    sql = dedent(f"""
        WITH targets AS (
            SELECT id FROM event_logs
            WHERE timestamp < CURRENT_DATE - MAKE_INTERVAL(days => :delete_after_days)
                AND {where_clause}
            LIMIT :batch_limit
        )
        DELETE FROM event_logs WHERE id IN (SELECT id FROM targets)
    """)
    start = time.monotonic()
    with engine.begin() as conn:
        conn.execute(text(f"SET LOCAL statement_timeout = '{_TXN_TIMEOUT_SECONDS}s'"))
        result = conn.execute(
            text(sql),
            {"delete_after_days": delete_after_days, "batch_limit": batch_limit},
        )
        rows = result.rowcount or 0
    duration = time.monotonic() - start
    logger.info(
        "[%s] Deleted %d rows (after_days=%d, limit=%d) in %.1fs",
        label,
        rows,
        delete_after_days,
        batch_limit,
        duration,
    )
    return rows, duration
