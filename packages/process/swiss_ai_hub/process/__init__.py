from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.process.agentic_processes.agentic_process import AgenticProcess
    from swiss_ai_hub.process.context.walkthrough.walkthrough_context import WalkthroughContext
    from swiss_ai_hub.process.delegators.agent.agent import Agent
    from swiss_ai_hub.process.delegators.human.human import Human
    from swiss_ai_hub.process.delegators.process.process import Process
    from swiss_ai_hub.process.delegators.program.program import Program
    from swiss_ai_hub.process.dispatchers.process_dispatcher import ProcessDispatcher
    from swiss_ai_hub.process.i18n.process_locale_handler import ProcessLocaleHandler
    from swiss_ai_hub.process.i18n.process_locale_string import ProcessLocaleString
    from swiss_ai_hub.process.process.decorators.process_step import process_step
    from swiss_ai_hub.process.runners.process_runner import ProcessRunner
    from swiss_ai_hub.process.runners.process_test_runner import ObservedEvent, ProcessTestRunner

__all__ = [
    "Agent",
    "AgenticProcess",
    "Human",
    "ObservedEvent",
    "Process",
    "ProcessDispatcher",
    "ProcessLocaleHandler",
    "ProcessLocaleString",
    "ProcessRunner",
    "ProcessTestRunner",
    "Program",
    "WalkthroughContext",
    "process_step",
]

_LAZY_IMPORTS: dict[str, str] = {
    "Agent": "swiss_ai_hub.process.delegators.agent.agent",
    "AgenticProcess": "swiss_ai_hub.process.agentic_processes.agentic_process",
    "Human": "swiss_ai_hub.process.delegators.human.human",
    "ObservedEvent": "swiss_ai_hub.process.runners.process_test_runner",
    "Process": "swiss_ai_hub.process.delegators.process.process",
    "ProcessDispatcher": "swiss_ai_hub.process.dispatchers.process_dispatcher",
    "ProcessLocaleHandler": "swiss_ai_hub.process.i18n.process_locale_handler",
    "ProcessLocaleString": "swiss_ai_hub.process.i18n.process_locale_string",
    "ProcessRunner": "swiss_ai_hub.process.runners.process_runner",
    "ProcessTestRunner": "swiss_ai_hub.process.runners.process_test_runner",
    "Program": "swiss_ai_hub.process.delegators.program.program",
    "WalkthroughContext": "swiss_ai_hub.process.context.walkthrough.walkthrough_context",
    "process_step": "swiss_ai_hub.process.process.decorators.process_step",
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
