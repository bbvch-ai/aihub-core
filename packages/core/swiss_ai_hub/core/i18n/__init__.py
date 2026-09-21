from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
    from swiss_ai_hub.core.i18n.locale_string import LOCALES, LocaleString

__all__ = [
    "LOCALES",
    "LocaleHandler",
    "LocaleString",
]

_LAZY_IMPORTS = {
    "LOCALES": "swiss_ai_hub.core.i18n.locale_string",
    "LocaleHandler": "swiss_ai_hub.core.i18n.locale_handler",
    "LocaleString": "swiss_ai_hub.core.i18n.locale_string",
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        from importlib import import_module

        value = getattr(import_module(_LAZY_IMPORTS[name]), name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
