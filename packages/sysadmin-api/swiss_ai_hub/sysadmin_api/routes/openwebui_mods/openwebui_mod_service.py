import json

import httpx
from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModHost, OpenWebuiModManifest, OpenWebuiModPackage, OpenWebuiModStore, OpenWebuiSettings,
)
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModPublicationEntity, OpenWebuiModRevisionEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_catalog_entry import OpenWebuiModCatalogEntry
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_publication_response import (
    OpenWebuiModPublicationResponse,
)

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_revision_response import (
    OpenWebuiModRevisionResponse,
)


class OpenWebuiModService:
    @staticmethod
    async def catalog(offset: int, limit: int) -> list[OpenWebuiModCatalogEntry]:
        builtins = OpenWebuiModBundles.packages()
        custom_ids = await run_in_threadpool(OpenWebuiModRevisionEntity.list_mod_ids)
        mod_ids = sorted(set(custom_ids) | builtins.keys())[offset:offset + limit]
        entries = []
        for mod_id in mod_ids:
            if package := builtins.get(mod_id):
                entries.append(OpenWebuiModCatalogEntry(
                    source_revision=package.revision, manifest=package.manifest, builtin=True,
                ))
            else:
                latest = await run_in_threadpool(OpenWebuiModRevisionEntity.latest_revision, mod_id)
                if latest is not None:
                    entries.append(OpenWebuiModCatalogEntry(
                        source_revision=latest.revision,
                        manifest=OpenWebuiModManifest.model_validate_json(latest.manifest_json), builtin=False,
                    ))
        return entries

    @staticmethod
    async def get_host() -> OpenWebuiModHost:
        try:
            return await OpenWebuiModHost.load(OpenWebuiSettings().BASE_URL)
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(status_code=503, detail="The compatible Open WebUI mod host is unavailable.") from error

    @staticmethod
    async def upload(content: bytes, uploaded_by: str, client: S3Client) -> OpenWebuiModRevisionResponse:
        try:
            package = OpenWebuiModPackage.from_zip(content)
            builtin = OpenWebuiModBundles.packages().get(package.manifest.id)
            if builtin is not None and package.revision != builtin.revision:
                raise ValueError("Built-in mod IDs are reserved. Choose a different ID for a custom mod.")
            entity = await OpenWebuiModStore(client).upload(content, uploaded_by)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return OpenWebuiModRevisionResponse.from_entity(entity)

    @staticmethod
    async def list_revisions(
        mod_id: str | None, offset: int, limit: int,
    ) -> list[OpenWebuiModRevisionResponse]:
        entities = await run_in_threadpool(OpenWebuiModRevisionEntity.list_revisions, mod_id, offset, limit)
        return [OpenWebuiModRevisionResponse.from_entity(entity) for entity in entities]

    @staticmethod
    async def get_revision(revision: str) -> OpenWebuiModRevisionResponse:
        entity = await run_in_threadpool(OpenWebuiModRevisionEntity.find_revision, revision)
        if entity is None:
            raise HTTPException(status_code=404, detail="Open WebUI mod revision not found.")
        return OpenWebuiModRevisionResponse.from_entity(entity)

    @classmethod
    async def publish(
        cls, source_revision: str, published_by: str, client: S3Client
    ) -> OpenWebuiModPublicationResponse:
        await cls.get_revision(source_revision)
        host = await cls.get_host()
        store = OpenWebuiModStore(client)
        content = await cls._compile(await store.read_archive(source_revision))
        try:
            entity = await store.publish(content, source_revision, published_by, host)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return OpenWebuiModPublicationResponse.from_entity(entity)

    @staticmethod
    async def _compile(source: bytes) -> bytes:
        settings = OpenWebuiSettings()
        try:
            async with httpx.AsyncClient(timeout=75) as client:
                async with client.stream(
                    "POST", settings.BASE_URL.rstrip("/") + "/_aihub/mods/control/compile", content=source,
                    headers={"Authorization": f"Bearer {settings.SCIM_TOKEN.get_secret_value()}",
                             "Content-Type": "application/zip"},
                ) as response:
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES:
                            raise HTTPException(502, "Open WebUI returned an oversized compilation result")
                    if response.status_code >= 400:
                        try:
                            detail = json.loads(content)["detail"]
                        except (ValueError, KeyError, TypeError) as error:
                            raise HTTPException(502, "Open WebUI returned an invalid compiler error") from error
                        raise HTTPException(response.status_code, detail)
                    if response.headers.get("content-type", "").split(";", 1)[0] != "application/zip":
                        raise HTTPException(502, "Open WebUI did not return a compiled mod archive")
                    return bytes(content)
        except httpx.HTTPError as error:
            raise HTTPException(503, "The Open WebUI mod compiler is unavailable") from error

    @classmethod
    async def list_publications(cls, source_revision: str) -> list[OpenWebuiModPublicationResponse]:
        await cls.get_revision(source_revision)
        entities = await run_in_threadpool(OpenWebuiModPublicationEntity.list_publications, source_revision)
        return [OpenWebuiModPublicationResponse.from_entity(entity) for entity in entities]

    @staticmethod
    async def get_publication(revision: str) -> OpenWebuiModPublicationResponse:
        entity = await run_in_threadpool(OpenWebuiModPublicationEntity.find_publication, revision)
        if entity is None:
            raise HTTPException(status_code=404, detail="Open WebUI mod publication not found.")
        return OpenWebuiModPublicationResponse.from_entity(entity)
