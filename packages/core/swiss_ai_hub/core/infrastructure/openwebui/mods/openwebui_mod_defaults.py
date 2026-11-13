from copy import deepcopy

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration import OpenWebuiModConfiguration
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_selection import OpenWebuiModSelection
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_settings import OpenWebuiModSettings


class OpenWebuiModDefaults:
    """Deployment defaults apply only until a tenant saves its own mod configuration."""

    @staticmethod
    def configuration() -> OpenWebuiModConfiguration:
        enabled = OpenWebuiModSettings().DEFAULTS
        builtins = OpenWebuiModBundles.packages()
        if unknown := set(enabled) - builtins.keys():
            raise ValueError(f"OPENWEBUI_MODS_DEFAULTS contains unknown bundled mod IDs: {', '.join(sorted(unknown))}")
        mod_ids = enabled + [mod_id for mod_id in builtins if mod_id not in enabled]
        return OpenWebuiModConfiguration(
            mods=[
                OpenWebuiModSelection(
                    mod_id=mod_id,
                    enabled=mod_id in enabled,
                    settings=deepcopy(builtins[mod_id].manifest.default_settings),
                )
                for mod_id in mod_ids
            ]
        )
