from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.events.process.discovery.agent_in.AgentInSpecs import AgentInSpecs
    from swiss_ai_hub.core.events.process.discovery.human_in.HumanInSpecs import HumanInSpecs
    from swiss_ai_hub.core.events.process.discovery.ProcessClassDiscoveryResponseEvent import (
        ProcessClassDiscoveryResponseEvent,
    )
    from swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecs import ProcessConfigSpecs
    from swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecsEntity import ProcessConfigSpecsEntity
    from swiss_ai_hub.core.events.process.discovery.program_in.ProgramInSpecs import ProgramInSpecs
    from swiss_ai_hub.core.events.process.exception.ProcessExceptionEvent import ProcessExceptionEvent
    from swiss_ai_hub.core.events.process.ProcessEvent import ProcessEvent
    from swiss_ai_hub.core.events.process.start.ProcessStartEvent import ProcessStartEvent
    from swiss_ai_hub.core.events.process.stop.ProcessStopEvent import ProcessStopEvent
    from swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent import AgentWorkEvent
    from swiss_ai_hub.core.events.process.work.human.HumanWorkEvent import HumanWorkEvent
    from swiss_ai_hub.core.events.process.work.process.ProcessWorkEvent import ProcessWorkEvent
    from swiss_ai_hub.core.events.process.work.program.ProgramWorkEvent import ProgramWorkEvent
    from swiss_ai_hub.core.events.process.work.WorkEvent import WorkEvent
    from swiss_ai_hub.core.events.process.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.human.HumanWorkRequestEvent import HumanWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.program.ProgramWorkRequestEvent import ProgramWorkRequestEvent
    from swiss_ai_hub.core.events.process.work_request.WorkRequestEvent import WorkRequestEvent

__all__ = [
    "AgentInSpecs",
    "AgentWorkEvent",
    "AgentWorkRequestEvent",
    "HumanInSpecs",
    "HumanWorkEvent",
    "HumanWorkRequestEvent",
    "ProcessClassDiscoveryResponseEvent",
    "ProcessConfigSpecs",
    "ProcessConfigSpecsEntity",
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
    "AgentInSpecs": "swiss_ai_hub.core.events.process.discovery.agent_in.AgentInSpecs",
    "AgentWorkEvent": "swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent",
    "AgentWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.agent.AgentWorkRequestEvent",
    "HumanInSpecs": "swiss_ai_hub.core.events.process.discovery.human_in.HumanInSpecs",
    "HumanWorkEvent": "swiss_ai_hub.core.events.process.work.human.HumanWorkEvent",
    "HumanWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.human.HumanWorkRequestEvent",
    "ProcessClassDiscoveryResponseEvent": "swiss_ai_hub.core.events.process.discovery.ProcessClassDiscoveryResponseEvent",
    "ProcessConfigSpecs": "swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecs",
    "ProcessConfigSpecsEntity": "swiss_ai_hub.core.events.process.discovery.ProcessConfigSpecsEntity",
    "ProcessEvent": "swiss_ai_hub.core.events.process.ProcessEvent",
    "ProcessExceptionEvent": "swiss_ai_hub.core.events.process.exception.ProcessExceptionEvent",
    "ProcessStartEvent": "swiss_ai_hub.core.events.process.start.ProcessStartEvent",
    "ProcessStopEvent": "swiss_ai_hub.core.events.process.stop.ProcessStopEvent",
    "ProcessWorkEvent": "swiss_ai_hub.core.events.process.work.process.ProcessWorkEvent",
    "ProgramInSpecs": "swiss_ai_hub.core.events.process.discovery.program_in.ProgramInSpecs",
    "ProgramWorkEvent": "swiss_ai_hub.core.events.process.work.program.ProgramWorkEvent",
    "ProgramWorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.program.ProgramWorkRequestEvent",
    "WorkEvent": "swiss_ai_hub.core.events.process.work.WorkEvent",
    "WorkRequestEvent": "swiss_ai_hub.core.events.process.work_request.WorkRequestEvent",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
