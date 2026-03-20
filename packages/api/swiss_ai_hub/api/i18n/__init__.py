from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
    from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString

__all__ = [
    "ApiLocaleHandler",
    "ApiLocaleString",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ApiLocaleHandler": "swiss_ai_hub.api.i18n.api_locale_handler",
    "ApiLocaleString": "swiss_ai_hub.api.i18n.api_locale_string",
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
