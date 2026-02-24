from datetime import datetime

import dagster as dg

from aihub_backup.dagster.schedules import daily_backup_schedule


def test_daily_backup_schedule_partition_key() -> None:
    """Schedule produces a RunRequest with today's date as partition key."""
    scheduled_time = datetime(2026, 2, 19, 2, 0, 0)
    context = dg.build_schedule_context(scheduled_execution_time=scheduled_time)

    result = daily_backup_schedule(context)

    assert isinstance(result, dg.RunRequest)
    assert result.partition_key == "2026-02-19"


def test_daily_backup_schedule_uses_online_mode() -> None:
    """Schedule always uses online mode."""
    scheduled_time = datetime(2026, 3, 1, 2, 0, 0)
    context = dg.build_schedule_context(scheduled_execution_time=scheduled_time)

    result = daily_backup_schedule(context)

    assert isinstance(result, dg.RunRequest)
    assert result.run_config is not None
    # RunConfig is serialized to a dict inside RunRequest
    run_config = result.run_config
    assert run_config["ops"]["create_backup"]["config"]["mode"] == "online"  # type: ignore[index]
