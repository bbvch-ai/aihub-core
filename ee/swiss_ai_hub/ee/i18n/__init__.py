from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.ee.i18n.enterprise_locale_handler import EnterpriseLocaleHandler
    from swiss_ai_hub.ee.i18n.enterprise_locale_string import EnterpriseLocaleString

__all__ = ["EnterpriseLocaleHandler", "EnterpriseLocaleString"]

_LAZY_IMPORTS: dict[str, str] = {
    "EnterpriseLocaleHandler": "swiss_ai_hub.ee.i18n.enterprise_locale_handler",
    "EnterpriseLocaleString": "swiss_ai_hub.ee.i18n.enterprise_locale_string",
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
