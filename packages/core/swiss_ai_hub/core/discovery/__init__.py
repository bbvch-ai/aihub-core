from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.discovery.discovery_kind import DiscoveryKind
    from swiss_ai_hub.core.discovery.discovery_settings import DiscoverySettings

__all__ = [
    "DiscoveryKind",
    "DiscoverySettings",
]

_LAZY_IMPORTS: dict[str, str] = {
    "DiscoveryKind": "swiss_ai_hub.core.discovery.discovery_kind",
    "DiscoverySettings": "swiss_ai_hub.core.discovery.discovery_settings",
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
