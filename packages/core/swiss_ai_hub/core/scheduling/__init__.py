from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.scheduling.agent_schedule import AgentSchedule
    from swiss_ai_hub.core.scheduling.cron_schedule_calculator import CronScheduleCalculator
    from swiss_ai_hub.core.scheduling.schedule_state_store import ScheduleStateStore
    from swiss_ai_hub.core.scheduling.scheduled_agent_service import ScheduledAgentService

__all__ = [
    "AgentSchedule",
    "CronScheduleCalculator",
    "ScheduleStateStore",
    "ScheduledAgentService",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentSchedule": "swiss_ai_hub.core.scheduling.agent_schedule",
    "CronScheduleCalculator": "swiss_ai_hub.core.scheduling.cron_schedule_calculator",
    "ScheduleStateStore": "swiss_ai_hub.core.scheduling.schedule_state_store",
    "ScheduledAgentService": "swiss_ai_hub.core.scheduling.scheduled_agent_service",
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
