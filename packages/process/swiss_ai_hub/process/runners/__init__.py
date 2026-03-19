from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.process.runners.process_runner import ProcessRunner
    from swiss_ai_hub.process.runners.process_test_runner import ObservedEvent, ProcessTestRunner

__all__ = [
    "ObservedEvent",
    "ProcessRunner",
    "ProcessTestRunner",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ObservedEvent": "swiss_ai_hub.process.runners.process_test_runner",
    "ProcessRunner": "swiss_ai_hub.process.runners.process_runner",
    "ProcessTestRunner": "swiss_ai_hub.process.runners.process_test_runner",
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
