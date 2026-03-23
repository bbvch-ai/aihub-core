from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.context.run.run_context import RunContext
    from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext

__all__ = [
    "RunContext",
    "ThreadContext",
]

_LAZY_IMPORTS: dict[str, str] = {
    "RunContext": "swiss_ai_hub.agent.context.run.run_context",
    "ThreadContext": "swiss_ai_hub.agent.context.thread.thread_context",
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
