from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration import OpenWebuiModConfiguration
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection import OpenWebuiModSelection


class OpenWebuiModDefaults:
    """New tenants follow installed built-ins; creating settings never compiles or publishes code."""

    @classmethod
    def configuration(cls) -> OpenWebuiModConfiguration:
        return OpenWebuiModConfiguration(mods=[
            OpenWebuiModSelection(
                mod_id=mod_id, enabled=mod_id in OpenWebuiModBundles.DEFAULT_ENABLED,
                settings=package.manifest.default_settings,
            )
            for mod_id, package in OpenWebuiModBundles.packages().items()
        ])
