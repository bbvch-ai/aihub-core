from typing import Annotated, Self

from fastapi import Depends, HTTPException, Path, Query, Request, Response, Security
from mypy_boto3_s3 import S3Client
from swiss_ai_hub.core.auth import AuthHandler, UserIdentity
from swiss_ai_hub.core.infrastructure import use_s3
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModConfiguration, OpenWebuiModHost, OpenWebuiModPackage, OpenWebuiModStore,
)
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.sysadmin_api.i18n import SysadminApiLocaleString
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_catalog_entry import OpenWebuiModCatalogEntry
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_publication_response import (
    OpenWebuiModPublicationResponse,
)
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_revision_response import (
    OpenWebuiModRevisionResponse,
)
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_configuration_service import (
    OpenWebuiModConfigurationService,
)
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_initialization_service import OpenWebuiModInitializationService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_global_service import OpenWebuiModGlobalService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_global_state import OpenWebuiModGlobalState

Revision = Annotated[str, Path(pattern=r"^[a-f0-9]{64}$")]


class OpenWebuiModController(Controller):
    name = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.openwebui_mods.name")
    description = SysadminApiLocaleString.from_i18n_path("sysadmin.controllers.openwebui_mods.description")
    icon = "mage:puzzle-piece"

    def __init__(self, *, auth: AuthHandler, route: str = "/admin/openwebui-mods"):
        super().__init__(auth=auth, route=route)

    def get_host(self, route: str = "/host") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_host(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModHost:
            return await OpenWebuiModService.get_host()

        return self

    def catalog(self, route: str = "/catalog") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_openwebui_mod_catalog(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            offset: Annotated[int, Query(ge=0)] = 0,
            limit: Annotated[int, Query(ge=1, le=100)] = 50,
        ) -> list[OpenWebuiModCatalogEntry]:
            return await OpenWebuiModService.catalog(offset, limit)

        return self

    def get_builtins(self, route: str = "/builtins") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_builtins(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> list[OpenWebuiModRevisionResponse]:
            return await OpenWebuiModInitializationService.builtins(client)

        return self

    def initialize(self, route: str = "/initialize") -> Self:
        @self.router.post(route, tags=self.tags, status_code=204)
        async def initialize_openwebui_mods(
            revisions: dict[str, str],
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> None:
            await OpenWebuiModInitializationService.initialize(revisions)

        return self

    def get_configuration(self, route: str = "/tenants/{tenant_id}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_configuration(
            tenant_id: str,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModConfiguration:
            return await OpenWebuiModConfigurationService.get(tenant_id)

        return self

    def global_configuration(self, route: str = "/global") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_global_mods(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.get()

        @self.router.put(route, tags=self.tags)
        async def replace_openwebui_global_mods(
            configuration: OpenWebuiModConfiguration,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.replace(configuration, client)

        @self.router.post(route + "/reconcile", tags=self.tags)
        async def reconcile_openwebui_global_mods(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModGlobalState:
            return await OpenWebuiModGlobalService.reconcile(client)

        @self.router.post(route + "/restart", tags=self.tags, status_code=202)
        async def restart_openwebui_for_mods(
            version: Annotated[int, Query(ge=0)],
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> dict[str, str | int]:
            return await OpenWebuiModGlobalService.restart(version)

        return self

    def replace_configuration(self, route: str = "/tenants/{tenant_id}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def replace_openwebui_mod_configuration(
            tenant_id: str,
            configuration: OpenWebuiModConfiguration,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModConfiguration:
            """Saves the complete selection for the next chat load. Version prevents lost updates."""
            return await OpenWebuiModConfigurationService.replace(tenant_id, configuration)

        return self

    def upload(self, route: str = "/revisions") -> Self:
        @self.router.post(
            route,
            tags=self.tags,
            openapi_extra={
                "requestBody": {
                    "required": True,
                    "content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}},
                }
            },
        )
        async def upload_openwebui_mod(
            request: Request,
            user: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModRevisionResponse:
            """Stores a validated source archive. Does not compile, publish or execute it."""
            content = await self._read_upload(request)
            return await OpenWebuiModService.upload(content, user.id, client)

        return self

    def list_revisions(self, route: str = "/revisions") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_openwebui_mod_revisions(
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            mod_id: Annotated[str | None, Query(max_length=64)] = None,
            offset: Annotated[int, Query(ge=0)] = 0,
            limit: Annotated[int, Query(ge=1, le=100)] = 50,
        ) -> list[OpenWebuiModRevisionResponse]:
            return await OpenWebuiModService.list_revisions(mod_id, offset, limit)

        return self

    def get_revision(self, route: str = "/revisions/{revision}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_revision(
            revision: Revision,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModRevisionResponse:
            return await OpenWebuiModService.get_revision(revision)

        return self

    def download(self, route: str = "/revisions/{revision}/source") -> Self:
        @self.router.get(
            route,
            tags=self.tags,
            response_class=Response,
            responses={200: {"content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}}},
        )
        async def download_openwebui_mod_source(
            revision: Revision,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> Response:
            record = await OpenWebuiModService.get_revision(revision)
            content = await OpenWebuiModStore(client).read_archive(revision)
            return self._zip_response(content, f"{record.manifest.id}-{revision}.zip")

        return self

    def publish(self, route: str = "/revisions/{revision}/publications") -> Self:
        @self.router.post(route, tags=self.tags)
        async def publish_openwebui_mod(
            revision: Revision,
            user: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> OpenWebuiModPublicationResponse:
            return await OpenWebuiModService.publish(revision, user.id, client)

        return self

    def list_publications(self, route: str = "/revisions/{revision}/publications") -> Self:
        @self.router.get(route, tags=self.tags)
        async def list_openwebui_mod_publications(
            revision: Revision,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> list[OpenWebuiModPublicationResponse]:
            return await OpenWebuiModService.list_publications(revision)

        return self

    def get_publication(self, route: str = "/publications/{revision}") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_openwebui_mod_publication(
            revision: Revision,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
        ) -> OpenWebuiModPublicationResponse:
            return await OpenWebuiModService.get_publication(revision)

        return self

    def download_publication(self, route: str = "/publications/{revision}/bundle") -> Self:
        @self.router.get(
            route,
            tags=self.tags,
            response_class=Response,
            responses={200: {"content": {"application/zip": {"schema": {"type": "string", "format": "binary"}}}}},
        )
        async def download_openwebui_mod_publication(
            revision: Revision,
            _: Annotated[UserIdentity, Security(self.sys_admin_user())],
            client: Annotated[S3Client, Depends(use_s3)],
        ) -> Response:
            record = await OpenWebuiModService.get_publication(revision)
            content = await OpenWebuiModStore(client).read_publication(revision)
            return self._zip_response(content, f"{record.mod_id}-{revision}-frontend.zip")

        return self

    @staticmethod
    def _zip_response(content: bytes, filename: str) -> Response:
        return Response(
            content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

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
