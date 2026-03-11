from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
    from swiss_ai_hub.agent.workflow.decorators.step import step

__all__ = [
    "precondition",
    "step",
]

_LAZY_IMPORTS: dict[str, str] = {
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
