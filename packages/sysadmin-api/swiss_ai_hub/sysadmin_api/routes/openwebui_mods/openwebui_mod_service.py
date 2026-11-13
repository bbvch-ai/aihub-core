import json

import httpx
from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModHost, OpenWebuiModManifest, OpenWebuiModPackage,
    OpenWebuiModPublicationManifest, OpenWebuiModStore, OpenWebuiSettings,
)
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_catalog_entry import OpenWebuiModCatalogEntry
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_upload_preview import OpenWebuiModUploadPreview


class OpenWebuiModService:
    @staticmethod
    async def catalog(offset: int, limit: int) -> list[OpenWebuiModCatalogEntry]:
        builtins = OpenWebuiModBundles.packages()
        installed = await run_in_threadpool(OpenWebuiModEntity.installed)
        return [OpenWebuiModCatalogEntry.from_entity(mod, builtin=mod.mod_id in builtins)
                for mod in installed[offset:offset + limit]]

    @staticmethod
    async def get_host() -> OpenWebuiModHost:
        try:
            return await OpenWebuiModHost.load(OpenWebuiSettings().BASE_URL)
        except (httpx.HTTPError, ValueError) as error:
            raise HTTPException(status_code=503, detail="The compatible Open WebUI mod host is unavailable.") from error

    @staticmethod
    def _package(content: bytes) -> OpenWebuiModPackage:
        try:
            package = OpenWebuiModPackage.from_zip(content)
            if package.manifest.id in OpenWebuiModBundles.packages():
                raise ValueError("Built-in mod IDs are reserved. Choose a different ID for a custom mod.")
            return package
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @classmethod
    async def inspect(cls, content: bytes) -> OpenWebuiModUploadPreview:
        package = await run_in_threadpool(cls._package, content)
        installed = await run_in_threadpool(OpenWebuiModEntity.find_mod, package.manifest.id)
        return OpenWebuiModUploadPreview(
            manifest=package.manifest,
            installed_version=OpenWebuiModManifest.model_validate_json(installed.manifest_json).version if installed else None,
        )

    @classmethod
    async def install(cls, content: bytes, installed_by: str, client: S3Client, *, replace: bool) -> OpenWebuiModCatalogEntry:
        package = await run_in_threadpool(cls._package, content)
        if not replace and await run_in_threadpool(OpenWebuiModEntity.find_mod, package.manifest.id) is not None:
            raise HTTPException(409, "A mod with this ID is already installed. Confirm replacement before updating it.")
        host = await cls.get_host()
        return await cls._install(content, installed_by, client, host, builtin=False)

    @classmethod
    async def install_builtin(cls, mod_id: str, client: S3Client) -> OpenWebuiModCatalogEntry:
        package = OpenWebuiModBundles.packages().get(mod_id)
        if package is None:
            raise HTTPException(404, "Built-in mod not found.")
        installed = await run_in_threadpool(OpenWebuiModEntity.find_mod, mod_id)
        host = await cls.get_host()
        if (installed is not None and installed.source_revision == package.revision
                and OpenWebuiModPublicationManifest.model_validate_json(installed.publication_manifest_json).compatibility == host.compatibility):
            await OpenWebuiModStore(client).prune()
            return OpenWebuiModCatalogEntry.from_entity(installed, builtin=True)
        content = OpenWebuiModBundles.zip(package.files)
        return await cls._install(content, "aihub-bundled", client, host, builtin=True)

    @classmethod
    async def _install(
        cls, content: bytes, installed_by: str, client: S3Client, host: OpenWebuiModHost, *, builtin: bool,
    ) -> OpenWebuiModCatalogEntry:
        compiled = await cls._compile(content)
        store = OpenWebuiModStore(client)
        try:
            installed = await store.install(content, compiled, installed_by, host)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        finally:
            await store.prune()
        return OpenWebuiModCatalogEntry.from_entity(installed, builtin=builtin)

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
