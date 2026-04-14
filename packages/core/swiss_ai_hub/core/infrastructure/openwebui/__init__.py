from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
    from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

__all__ = [
    "AccessGrant",
    "OnlineAgent",
    "OpenWebuiClient",
    "OpenWebuiProvisioner",
    "OpenWebuiSettings",
    "OpenWebuiTokenService",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AccessGrant": "swiss_ai_hub.core.infrastructure.openwebui.access_grant",
    "OnlineAgent": "swiss_ai_hub.core.infrastructure.openwebui.online_agent",
    "OpenWebuiClient": "swiss_ai_hub.core.infrastructure.openwebui.openwebui_client",
    "OpenWebuiProvisioner": "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner",
    "OpenWebuiSettings": "swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings",
    "OpenWebuiTokenService": "swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service",
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
