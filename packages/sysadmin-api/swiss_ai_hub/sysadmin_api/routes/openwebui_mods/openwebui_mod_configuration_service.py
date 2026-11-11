from fastapi import HTTPException
from keycloak import KeycloakGetError
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModConfiguration, OpenWebuiModDefaults, OpenWebuiModResolver,
)
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModRevisionEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService


class OpenWebuiModConfigurationService:
    @staticmethod
    async def _tenant(tenant_id: str) -> TenantMetadataEntity:
        tenant = await run_in_threadpool(TenantMetadataEntity.get_metadata_by_tenant_id, tenant_id)
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        return tenant

    @classmethod
    async def get(cls, tenant_id: str) -> OpenWebuiModConfiguration:
        tenant = await cls._tenant(tenant_id)
        if tenant.openwebui_mods_json is None:
            return OpenWebuiModDefaults.configuration()
        return cls._configuration(tenant)

    @staticmethod
    def _configuration(tenant: TenantMetadataEntity) -> OpenWebuiModConfiguration:
        if tenant.openwebui_mods_json is None:
            return OpenWebuiModConfiguration()
        return OpenWebuiModConfiguration.model_validate_json(tenant.openwebui_mods_json)

    @classmethod
    async def replace(cls, tenant_id: str, configuration: OpenWebuiModConfiguration) -> OpenWebuiModConfiguration:
        tenant = await cls._tenant(tenant_id)
        try:
            await KeycloakAdminService.get_tenant_group(tenant_id)
        except KeycloakGetError as error:
            if error.response_code != 404:
                raise
            raise HTTPException(status_code=409, detail="An orphaned tenant cannot be edited.") from error
        if configuration.version != cls._configuration(tenant).version:
            raise HTTPException(status_code=409, detail="Mod settings changed. Reload before saving.")
        await cls._validate_mods(configuration)
        updated = configuration.model_copy(update={"version": configuration.version + 1})
        saved = await run_in_threadpool(
            TenantMetadataEntity.replace_openwebui_mods, tenant_id, tenant.openwebui_mods_json, updated.model_dump_json()
        )
        if not saved:
            raise HTTPException(status_code=409, detail="Tenant or mod settings changed. Reload before saving.")
        return updated

    @staticmethod
    async def _validate_mods(configuration: OpenWebuiModConfiguration) -> None:
        builtins = OpenWebuiModBundles.packages()
        for mod in configuration.mods:
            if mod.mod_id in builtins and mod.publication is not None:
                raise HTTPException(status_code=422, detail=f"Built-in '{mod.mod_id}' follows AI Hub and cannot be pinned.")
            if mod.mod_id not in builtins and mod.publication is None:
                latest = await run_in_threadpool(OpenWebuiModRevisionEntity.latest_revision, mod.mod_id)
                if latest is None:
                    raise HTTPException(status_code=422, detail=f"Unknown mod '{mod.mod_id}'.")
        host = await OpenWebuiModService.get_host() if any(mod.enabled for mod in configuration.mods) else None
        if host is not None:
            try:
                enabled = await OpenWebuiModResolver.resolve(configuration, host.compatibility)
            except ValueError as error:
                raise HTTPException(status_code=409, detail=str(error)) from error
        else:
            enabled = OpenWebuiModConfiguration()
        for mod in configuration.mods:
            if mod.enabled or mod.mod_id in builtins or mod.publication is None:
                continue
            publication = await OpenWebuiModService.get_publication(mod.publication)
            if publication.mod_id != mod.mod_id:
                raise HTTPException(status_code=422, detail=f"Publication does not belong to mod '{mod.mod_id}'.")
        targets: dict[str, str] = {}
        for mod in enabled.mods:
            publication = await OpenWebuiModService.get_publication(mod.publication)
            source = await OpenWebuiModService.get_revision(publication.manifest.source_revision)
            if source.manifest.backend_restart_required or "open_webui.main:lifespan" in source.manifest.backend_overrides:
                raise HTTPException(status_code=422, detail=f"'{mod.mod_id}' requires global activation and an Open WebUI restart.")
            if publication.mod_id != mod.mod_id:
                raise HTTPException(status_code=422, detail=f"Publication does not belong to mod '{mod.mod_id}'.")
            assert host is not None
            manifest = publication.manifest
            if manifest.compatibility != host.compatibility:
                raise HTTPException(status_code=409, detail=f"Recompile '{mod.mod_id}' for the current Open WebUI host.")
            for target in manifest.replacements:
                if target not in host.components:
                    raise HTTPException(status_code=409, detail=f"Replacement target is absent: {target}")
                if target in targets:
                    raise HTTPException(
                        status_code=409, detail=f"Mods '{targets[target]}' and '{mod.mod_id}' both replace {target}."
                    )
                targets[target] = mod.mod_id
