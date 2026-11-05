from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.network.source_host_guard import SourceHostGuard

__all__ = [
    "SourceHostGuard",
]

_LAZY_IMPORTS = {
    "SourceHostGuard": "swiss_ai_hub.core.network.source_host_guard",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
