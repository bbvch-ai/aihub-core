import logging
from typing import Annotated, Self

from fastapi import Depends, HTTPException, Query, Request, Security
from mypy_boto3_s3 import S3Client
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.infrastructure import use_s3
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles,
    OpenWebuiModConfiguration,
    OpenWebuiModHost,
    OpenWebuiModPackage,
)
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.sysadmin_api.i18n import SysadminApiLocaleString
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_catalog_entry import OpenWebuiModCatalogEntry
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_global_state import OpenWebuiModGlobalState
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_upload_preview import OpenWebuiModUploadPreview
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_configuration_service import (
    OpenWebuiModConfigurationService,
)
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_global_service import OpenWebuiModGlobalService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService

ZIP_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "application/zip": {"schema": {"type": "string", "format": "binary"}},
        },
    }
}


class OpenWebuiModController(Controller):
    name = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.openwebui_mods.name")
    description = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.openwebui_mods.description")
    icon = "mage:puzzle-piece"

    def __init__(self, *, auth: AuthHandler, route: str = "/admin/openwebui-mods"):
        super().__init__(auth=auth, route=route)
        self._sys_admin_dependency = Security(self.sys_admin_user())
        self.router.dependencies.append(self._sys_admin_dependency)

    def get_host(self, route: str = "/host") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_host() -> OpenWebuiModHost:
            return await OpenWebuiModService.get_host()

        return self

    def catalog(self, route: str = "/catalog") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_openwebui_mod_catalog(
            offset: Annotated[int, Query(ge=0)] = 0,
            limit: Annotated[int, Query(ge=1, le=100)] = 50,
        ) -> list[OpenWebuiModCatalogEntry]:
            return await OpenWebuiModService.catalog(offset, limit)

        return self

    def get_builtins(self, route: str = "/builtins") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_builtins() -> list[str]:
            return list(OpenWebuiModBundles.packages())

        return self

    def install_builtin(self, route: str = "/builtins/{mod_id}/install") -> Self:
        @self.router.post(route, tags=self.tags)
        async def install_openwebui_builtin_mod(
            mod_id: str,
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModCatalogEntry:
            return await OpenWebuiModService.install_builtin(mod_id, client)

        return self

    def get_configuration(self, route: str = "/tenants/{tenant_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_configuration(tenant_id: str) -> OpenWebuiModConfiguration:
            return await OpenWebuiModConfigurationService.get(tenant_id)

        return self

    def global_configuration(self, route: str = "/global") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_global_mods() -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.get()

        @self.router.put(route, tags=self.tags)
        async def replace_openwebui_global_mods(
            configuration: OpenWebuiModConfiguration,
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.replace(configuration, client)

        @self.router.post(route + "/reconcile", tags=self.tags)
        async def reconcile_openwebui_global_mods(
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.reconcile(client)

        @self.router.post(route + "/restart", tags=self.tags, status_code=202)
        async def restart_openwebui_for_mods(
            version: Annotated[int, Query(ge=0)],
        ) -> dict[str, str | int]:
            return await OpenWebuiModGlobalService.restart(version)

        return self

    def replace_configuration(self, route: str = "/tenants/{tenant_id}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def replace_openwebui_mod_configuration(
            tenant_id: str,
            configuration: OpenWebuiModConfiguration,
        ) -> OpenWebuiModConfiguration:
            """Saves the complete selection for the next chat load. Version prevents lost updates."""
            return await OpenWebuiModConfigurationService.replace(tenant_id, configuration)

        return self

    def inspect(self, route: str = "/inspect") -> Self:
        @self.router.post(route, tags=self.tags, openapi_extra=ZIP_BODY)
        async def inspect_openwebui_mod(request: Request) -> OpenWebuiModUploadPreview:
            return await OpenWebuiModService.inspect(await self._read_upload(request))

        return self

    def install(self, route: str = "/install") -> Self:
        @self.router.post(route, tags=self.tags, openapi_extra=ZIP_BODY)
        async def install_openwebui_mod(
            request: Request,
            user: Annotated[UserIdentity, self._sys_admin_dependency],
            client: Annotated[S3Client, Depends(use_s3)],
            replace: bool = False,
        ) -> OpenWebuiModCatalogEntry:
            installed = await OpenWebuiModService.install(
                await self._read_upload(request), user.id, client, replace=replace
            )
            try:
                await OpenWebuiModGlobalService.reconcile(client, mod_id=installed.manifest.id)
            except Exception:
                logging.getLogger(__name__).exception("Installed mod could not be reconciled with global activation")
                installed.warnings.append(
                    "Installed, but global activation could not be updated. Save Global Open WebUI settings to retry."
                )
            return installed

        return self

    @staticmethod
    async def _read_upload(request: Request) -> bytes:
        content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        if content_type not in {"application/zip", "application/octet-stream"}:
            raise HTTPException(status_code=415, detail="Upload the ZIP as the request body.")
        length = request.headers.get("content-length")
        if length and length.isdecimal() and int(length) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES:
            raise HTTPException(status_code=413, detail="Mod archive exceeds the 16 MiB upload limit.")
        content = bytearray()
        async for chunk in request.stream():
            if len(content) + len(chunk) > OpenWebuiModPackage.MAX_ARCHIVE_BYTES:
                raise HTTPException(status_code=413, detail="Mod archive exceeds the 16 MiB upload limit.")
            content.extend(chunk)
        return bytes(content)
