from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.scheduling.cron_schedule import CronSchedule
    from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
    from swiss_ai_hub.core.scheduling.cron_scheduler import CronScheduler
    from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore
    from swiss_ai_hub.core.scheduling.scheduler_settings import SchedulerSettings

__all__ = [
    "CronSchedule",
    "CronScheduleCalculator",
    "CronScheduler",
    "ScheduleStateStore",
    "SchedulerSettings",
]

_LAZY_IMPORTS: dict[str, str] = {
    "CronSchedule": "swiss_ai_hub.core.scheduling.cron_schedule",
    "CronScheduleCalculator": "swiss_ai_hub.core.scheduling.cron_schedule_calculator",
    "CronScheduler": "swiss_ai_hub.core.scheduling.cron_scheduler",
    "ScheduleStateStore": "swiss_ai_hub.core.scheduling.schedule_state_store",
    "SchedulerSettings": "swiss_ai_hub.core.scheduling.scheduler_settings",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
