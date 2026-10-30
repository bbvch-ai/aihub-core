from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.request_limits.api_request_limit_settings import ApiRequestLimitSettings
    from swiss_ai_hub.api.request_limits.json_body_size_limit_middleware import JsonBodySizeLimitMiddleware

__all__ = [
    "ApiRequestLimitSettings",
    "JsonBodySizeLimitMiddleware",
]

_LAZY_IMPORTS: dict[str, str] = {
    "ApiRequestLimitSettings": "swiss_ai_hub.api.request_limits.api_request_limit_settings",
    "JsonBodySizeLimitMiddleware": "swiss_ai_hub.api.request_limits.json_body_size_limit_middleware",
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
