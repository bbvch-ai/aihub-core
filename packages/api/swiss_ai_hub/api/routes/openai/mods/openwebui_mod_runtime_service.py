from typing import Literal

from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModCompatibility, OpenWebuiModConfiguration, OpenWebuiModDefaults,
    OpenWebuiModPublicationManifest, OpenWebuiModStore, OpenWebuiModResolver,
)
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModPublicationEntity

from swiss_ai_hub.api.routes.openai.mods.openwebui_mod_runtime_configuration import OpenWebuiModRuntimeConfiguration


class OpenWebuiModRuntimeService:
    @classmethod
    async def resolve_configuration(
        cls, user: UserIdentity, compatibility: OpenWebuiModCompatibility,
    ) -> OpenWebuiModRuntimeConfiguration:
        configuration = await cls._resolve_selection(user, compatibility)
        await cls._validate_publications(configuration, compatibility)
        return OpenWebuiModRuntimeConfiguration.from_configuration(cls._tenant_id(user), compatibility, configuration)

    @classmethod
    async def _resolve_selection(
        cls, user: UserIdentity, compatibility: OpenWebuiModCompatibility,
    ) -> OpenWebuiModConfiguration:
        configuration = await cls._configuration(user)
        try:
            return await OpenWebuiModResolver.resolve(configuration, compatibility)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @classmethod
    async def _configuration(cls, user: UserIdentity) -> OpenWebuiModConfiguration:
        tenant = await run_in_threadpool(TenantMetadataEntity.get_metadata_by_tenant_id, cls._tenant_id(user))
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant not found.")
        try:
            return (
                OpenWebuiModConfiguration.model_validate_json(tenant.openwebui_mods_json)
                if tenant.openwebui_mods_json is not None
                else OpenWebuiModDefaults.configuration()
            )
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @staticmethod
    def _tenant_id(user: UserIdentity) -> str:
        if user.acting_within_tenant is None:
            raise HTTPException(status_code=403, detail="Tenant context required.")
        return user.acting_within_tenant.id

    @staticmethod
    async def _publication(revision: str) -> OpenWebuiModPublicationEntity:
        publication = await run_in_threadpool(OpenWebuiModPublicationEntity.find_publication, revision)
        if publication is None:
            raise HTTPException(status_code=409, detail="A selected mod publication is missing. Reload after repair.")
        return publication

    @classmethod
    async def _validate_publications(
        cls, configuration: OpenWebuiModConfiguration, compatibility: OpenWebuiModCompatibility,
    ) -> None:
        targets: set[str] = set()
        for mod in configuration.mods:
            publication = await cls._publication(mod.publication)
            manifest = cls._validate_publication(publication, mod.mod_id, compatibility)
            if targets.intersection(manifest.replacements):
                raise HTTPException(status_code=409, detail="Selected mods have conflicting component replacements.")
            targets.update(manifest.replacements)

    @staticmethod
    def _validate_publication(
        publication: OpenWebuiModPublicationEntity, mod_id: str, compatibility: OpenWebuiModCompatibility,
    ) -> OpenWebuiModPublicationManifest:
        manifest = OpenWebuiModPublicationManifest.model_validate_json(publication.manifest_json)
        if publication.mod_id != mod_id or manifest.compatibility != compatibility:
            raise HTTPException(status_code=409, detail=f"Mod '{mod_id}' needs a compatible publication.")
        return manifest

    @classmethod
    async def authorize_publication(
        cls, user: UserIdentity, compatibility: OpenWebuiModCompatibility, revision: str,
    ) -> OpenWebuiModPublicationEntity:
        configuration = await cls._resolve_selection(user, compatibility)
        selected = next((mod for mod in configuration.mods if mod.publication == revision), None)
        if selected is None:
            raise HTTPException(status_code=403, detail="This publication is not selected for the tenant.")
        publication = await cls._publication(revision)
        cls._validate_publication(publication, selected.mod_id, compatibility)
        return publication

    @classmethod
    async def read_archive(
        cls, user: UserIdentity, compatibility: OpenWebuiModCompatibility, revision: str,
        kind: Literal["frontend", "source"], client: S3Client,
    ) -> bytes:
        publication = await cls.authorize_publication(user, compatibility, revision)
        store = OpenWebuiModStore(client)
        if kind == "source":
            return await store.read_archive(publication.source_revision)
        return await store.read_publication(revision)
