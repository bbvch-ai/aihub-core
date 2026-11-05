from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.request_limits.api_request_limit_settings import ApiRequestLimitSettings
    from swiss_ai_hub.api.request_limits.body_size_limit_middleware import BodySizeLimitMiddleware

__all__ = [
    "ApiRequestLimitSettings",
    "BodySizeLimitMiddleware",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ApiRequestLimitSettings": "swiss_ai_hub.api.request_limits.api_request_limit_settings",
    "BodySizeLimitMiddleware": "swiss_ai_hub.api.request_limits.body_size_limit_middleware",
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
