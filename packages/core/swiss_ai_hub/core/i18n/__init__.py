from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
    from swiss_ai_hub.core.i18n.LocaleString import LocaleString

__all__ = [
    "LocaleHandler",
    "LocaleString",
]

_LAZY_IMPORTS = {
    "LocaleHandler": "swiss_ai_hub.core.i18n.LocaleHandler",
    "LocaleString": "swiss_ai_hub.core.i18n.LocaleString",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        return getattr(import_module(_LAZY_IMPORTS[name]), name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
