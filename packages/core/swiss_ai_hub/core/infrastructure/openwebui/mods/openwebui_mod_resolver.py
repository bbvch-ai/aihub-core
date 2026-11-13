from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_activation import OpenWebuiModActivation
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration import OpenWebuiModConfiguration
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_manifest import OpenWebuiModManifest
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication_manifest import (
    OpenWebuiModPublicationManifest,
)
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_resolved_configuration import (
    OpenWebuiModResolvedConfiguration,
)
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_entity import OpenWebuiModEntity


class OpenWebuiModResolver:
    @staticmethod
    async def resolve(
        configuration: OpenWebuiModConfiguration,
        compatibility: OpenWebuiModCompatibility,
    ) -> OpenWebuiModResolvedConfiguration:
        installed = {mod.mod_id: mod for mod in await run_in_threadpool(OpenWebuiModEntity.installed)}
        builtins = OpenWebuiModBundles.packages()
        mods = []
        for selection in configuration.mods:
            if not selection.enabled:
                continue
            mod = installed.get(selection.mod_id)
            if mod is None:
                raise ValueError(
                    f"Mod '{selection.mod_id}' is not installed. Run mod initialization or upload its ZIP."
                )
            if selection.mod_id in builtins and builtins[selection.mod_id].revision != mod.source_revision:
                raise ValueError(f"Built-in '{selection.mod_id}' needs initialization for this AI Hub release.")
            manifest = OpenWebuiModManifest.model_validate_json(mod.manifest_json)
            if manifest.global_only:
                continue
            publication = OpenWebuiModPublicationManifest.model_validate_json(mod.publication_manifest_json)
            if publication.compatibility != compatibility:
                raise ValueError(f"Mod '{selection.mod_id}' needs installation for this Open WebUI host.")
            mods.append(
                OpenWebuiModActivation(
                    **selection.model_dump(),
                    publication=mod.publication,
                    has_backend=manifest.backend is not None,
                )
            )
        return OpenWebuiModResolvedConfiguration(version=configuration.version, mods=mods)
