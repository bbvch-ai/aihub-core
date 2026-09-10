from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.process.discovery.agent_in.agent_in_specs import AgentInSpecs
    from swiss_ai_hub.core.events.process.discovery.human_in.human_in_specs import HumanInSpecs
    from swiss_ai_hub.core.events.process.discovery.process_class_discovery_response_event import (
        ProcessClassDiscoveryResponseEvent,
    )
    from swiss_ai_hub.core.events.process.discovery.program_in.program_in_specs import ProgramInSpecs
    from swiss_ai_hub.core.events.process.exception.process_exception_event import ProcessExceptionEvent
    from swiss_ai_hub.core.events.process.process_event import ProcessEvent
    from swiss_ai_hub.core.events.process.start.process_start_event import ProcessStartEvent
    from swiss_ai_hub.core.events.process.stop.process_stop_event import ProcessStopEvent
    from swiss_ai_hub.core.events.process.work.agent.agent_work_event import AgentWorkEvent
    from swiss_ai_hub.core.events.process.work.human.human_work_event import HumanWorkEvent
    from swiss_ai_hub.core.events.process.work.process.process_work_event import ProcessWorkEvent
    from swiss_ai_hub.core.events.process.work.program.program_work_event import ProgramWorkEvent
    from swiss_ai_hub.core.events.process.work.work_event import WorkEvent
    from swiss_ai_hub.core.events.process.work_request.agent.agent_work_request_event import AgentWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.human.human_work_request_event import HumanWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.program.program_work_request_event import ProgramWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.work_request_event import WorkRequestEvent

__all__ = [
    "AgentInSpecs",
    "AgentWorkEvent",
    "AgentWorkRequestEvent",
    "HumanInSpecs",
    "HumanWorkEvent",
    "HumanWorkRequestEvent",
    "ProcessClassDiscoveryResponseEvent",
    "ProcessEvent",
    "ProcessExceptionEvent",
    "ProcessStartEvent",
    "ProcessStopEvent",
    "ProcessWorkEvent",
    "ProgramInSpecs",
    "ProgramWorkEvent",
    "ProgramWorkRequestEvent",
    "WorkEvent",
    "WorkRequestEvent",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AgentInSpecs": "swiss_ai_hub.core.events.process.discovery.agent_in.agent_in_specs",
    "AgentWorkEvent": "swiss_ai_hub.core.events.process.work.agent.agent_work_event",
    "AgentWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.agent.agent_work_request_event",
    "HumanInSpecs": "swiss_ai_hub.core.events.process.discovery.human_in.human_in_specs",
    "HumanWorkEvent": "swiss_ai_hub.core.events.process.work.human.human_work_event",
    "HumanWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.human.human_work_request_event",
    "ProcessClassDiscoveryResponseEvent": "swiss_ai_hub.core.events.process.discovery.process_class_discovery_response_event",
    "ProcessEvent": "swiss_ai_hub.core.events.process.process_event",
    "ProcessExceptionEvent": "swiss_ai_hub.core.events.process.exception.process_exception_event",
    "ProcessStartEvent": "swiss_ai_hub.core.events.process.start.process_start_event",
    "ProcessStopEvent": "swiss_ai_hub.core.events.process.stop.process_stop_event",
    "ProcessWorkEvent": "swiss_ai_hub.core.events.process.work.process.process_work_event",
    "ProgramInSpecs": "swiss_ai_hub.core.events.process.discovery.program_in.program_in_specs",
    "ProgramWorkEvent": "swiss_ai_hub.core.events.process.work.program.program_work_event",
    "ProgramWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.program.program_work_request_event",
    "WorkEvent": "swiss_ai_hub.core.events.process.work.work_event",
    "WorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.work_request_event",
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
