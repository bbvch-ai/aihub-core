from starlette.concurrency import run_in_threadpool

from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_bundles import OpenWebuiModBundles
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_compatibility import OpenWebuiModCompatibility
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_configuration import OpenWebuiModConfiguration
from swiss_ai_hub.core.infrastructure.openwebui.mods.openwebui_mod_publication_manifest import OpenWebuiModPublicationManifest
from swiss_ai_hub.core.persistence.openwebui.openwebui_mod_publication_entity import OpenWebuiModPublicationEntity


class OpenWebuiModResolver:
    @staticmethod
    async def publication(source_revision: str, compatibility: OpenWebuiModCompatibility) -> OpenWebuiModPublicationEntity | None:
        publications = await run_in_threadpool(OpenWebuiModPublicationEntity.list_publications, source_revision)
        return next((publication for publication in publications if
            OpenWebuiModPublicationManifest.model_validate_json(publication.manifest_json).compatibility == compatibility
        ), None)

    @classmethod
    async def resolve(
        cls, configuration: OpenWebuiModConfiguration, compatibility: OpenWebuiModCompatibility,
    ) -> OpenWebuiModConfiguration:
        resolved = configuration.model_copy(deep=True)
        resolved.mods = [mod for mod in resolved.mods if mod.enabled]
        builtins = OpenWebuiModBundles.packages()
        for mod in resolved.mods:
            if mod.mod_id in builtins:
                publication = await cls.publication(builtins[mod.mod_id].revision, compatibility)
                if publication is None:
                    raise ValueError(f"Built-in '{mod.mod_id}' is not initialized for this host. Run openwebui-mods-init.")
                mod.publication = publication.revision
            elif mod.publication is None:
                raise ValueError(f"Select a published version of '{mod.mod_id}' before enabling it.")
        return resolved
