from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.api.routes.webhook.dto.openwebui_webhook_payload import OpenWebuiWebhookPayload
    from swiss_ai_hub.api.routes.webhook.dto.openwebui_webhook_user import OpenWebuiWebhookUser
    from swiss_ai_hub.api.routes.webhook.dto.webhook_response import WebhookResponse

__all__ = [
    "OpenWebuiWebhookPayload",
    "OpenWebuiWebhookUser",
    "WebhookResponse",
]

_LAZY_IMPORTS: dict[str, str] = {
    "OpenWebuiWebhookPayload": "swiss_ai_hub.api.routes.webhook.dto.openwebui_webhook_payload",
    "OpenWebuiWebhookUser": "swiss_ai_hub.api.routes.webhook.dto.openwebui_webhook_user",
    "WebhookResponse": "swiss_ai_hub.api.routes.webhook.dto.webhook_response",
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
