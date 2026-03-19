from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.agents.agent import Agent
    from swiss_ai_hub.agent.context.run.run_context import RunContext
    from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
    from swiss_ai_hub.agent.dispatchers.agent_dispatcher import AgentDispatcher
    from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler
    from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
    from swiss_ai_hub.agent.runners.agent_runner import AgentRunner
    from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner, ObservedEvent
    from swiss_ai_hub.agent.runners.multiprocess_agent_runner import MultiprocessAgentRunner
    from swiss_ai_hub.agent.tracing.agent_run_tracer import AgentRunTracer
    from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
    from swiss_ai_hub.agent.workflow.decorators.step import step

__all__ = [
    "Agent",
    "AgentDispatcher",
    "AgentLocaleHandler",
    "AgentLocaleString",
    "AgentRunTracer",
    "AgentRunner",
    "AgentTestRunner",
    "MultiprocessAgentRunner",
    "ObservedEvent",
    "RunContext",
    "ThreadContext",
    "precondition",
    "step",
]

_LAZY_IMPORTS: dict[str, str] = {
    "Agent": "swiss_ai_hub.agent.agents.agent",
    "AgentDispatcher": "swiss_ai_hub.agent.dispatchers.agent_dispatcher",
    "AgentLocaleHandler": "swiss_ai_hub.agent.i18n.agent_locale_handler",
    "AgentLocaleString": "swiss_ai_hub.agent.i18n.agent_locale_string",
    "AgentRunTracer": "swiss_ai_hub.agent.tracing.agent_run_tracer",
    "AgentRunner": "swiss_ai_hub.agent.runners.agent_runner",
    "AgentTestRunner": "swiss_ai_hub.agent.runners.agent_test_runner",
    "MultiprocessAgentRunner": "swiss_ai_hub.agent.runners.multiprocess_agent_runner",
    "ObservedEvent": "swiss_ai_hub.agent.runners.agent_test_runner",
    "RunContext": "swiss_ai_hub.agent.context.run.run_context",
    "ThreadContext": "swiss_ai_hub.agent.context.thread.thread_context",
    "precondition": "swiss_ai_hub.agent.workflow.decorators.precondition",
    "step": "swiss_ai_hub.agent.workflow.decorators.step",
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
