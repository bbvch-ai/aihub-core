from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_activation import OpenWebuiModActivation
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration import OpenWebuiModConfiguration
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection import OpenWebuiModSelection
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_defaults import OpenWebuiModDefaults
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_host import OpenWebuiModHost
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package import OpenWebuiModPackage
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication import OpenWebuiModPublication
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication_manifest import (
        OpenWebuiModPublicationManifest,
    )
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_store import OpenWebuiModStore
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_resolved_configuration import OpenWebuiModResolvedConfiguration
    from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_resolver import OpenWebuiModResolver
    from swiss_ai_hub.core.infrastructure.openwebui.online_agent import OnlineAgent
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_settings import OpenWebuiSettings
    from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

__all__ = [
    "AccessGrant",
    "OnlineAgent",
    "OpenWebuiClient",
    "OpenWebuiModActivation",
    "OpenWebuiModBundles",
    "OpenWebuiModCompatibility",
    "OpenWebuiModConfiguration",
    "OpenWebuiModSelection",
    "OpenWebuiModDefaults",
    "OpenWebuiModHost",
    "OpenWebuiModManifest",
    "OpenWebuiModPackage",
    "OpenWebuiModPublication",
    "OpenWebuiModPublicationManifest",
    "OpenWebuiModStore",
    "OpenWebuiModResolvedConfiguration",
    "OpenWebuiModResolver",
    "OpenWebuiProvisioner",
    "OpenWebuiSettings",
    "OpenWebuiTokenService",
]

_LAZY_IMPORTS: dict[str, str] = {
    "AccessGrant": "swiss_ai_hub.core.infrastructure.openwebui.access_grant",
    "OnlineAgent": "swiss_ai_hub.core.infrastructure.openwebui.online_agent",
    "OpenWebuiClient": "swiss_ai_hub.core.infrastructure.openwebui.openwebui_client",
    "OpenWebuiModActivation": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_activation",
    "OpenWebuiModBundles": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles",
    "OpenWebuiModCompatibility": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility",
    "OpenWebuiModConfiguration": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration",
    "OpenWebuiModSelection": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection",
    "OpenWebuiModDefaults": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_defaults",
    "OpenWebuiModHost": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_host",
    "OpenWebuiModManifest": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest",
    "OpenWebuiModPackage": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_package",
    "OpenWebuiModPublication": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication",
    "OpenWebuiModPublicationManifest": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication_manifest",
    "OpenWebuiModStore": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_store",
    "OpenWebuiModResolvedConfiguration": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_resolved_configuration",
    "OpenWebuiModResolver": "swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_resolver",
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
