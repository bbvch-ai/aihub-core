from fastapi import HTTPException
from keycloak import KeycloakGetError
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModConfiguration,
    OpenWebuiModDefaults,
    OpenWebuiModPublicationManifest,
    OpenWebuiModResolver,
)
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

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
            TenantMetadataEntity.replace_openwebui_mods,
            tenant_id,
            tenant.openwebui_mods_json,
            updated.model_dump_json(),
        )
        if not saved:
            raise HTTPException(status_code=409, detail="Tenant or mod settings changed. Reload before saving.")
        return updated

    @staticmethod
    async def _validate_mods(configuration: OpenWebuiModConfiguration) -> None:
        for mod in configuration.mods:
            if await run_in_threadpool(OpenWebuiModEntity.find_mod, mod.mod_id) is None:
                raise HTTPException(422, f"Unknown mod '{mod.mod_id}'.")
        if not any(mod.enabled for mod in configuration.mods):
            return
        host = await OpenWebuiModService.get_host()
        try:
            enabled = await OpenWebuiModResolver.resolve(configuration, host.compatibility)
        except ValueError as error:
            raise HTTPException(409, str(error)) from error
        targets: dict[str, str] = {}
        for mod in enabled.mods:
            installed = await run_in_threadpool(OpenWebuiModEntity.find_mod, mod.mod_id)
            manifest = OpenWebuiModPublicationManifest.model_validate_json(installed.publication_manifest_json)
            for target in manifest.replacements:
                if target not in host.components:
                    raise HTTPException(409, f"Replacement target is absent: {target}")
                if target in targets:
                    raise HTTPException(409, f"Mods '{targets[target]}' and '{mod.mod_id}' both replace {target}.")
                targets[target] = mod.mod_id
