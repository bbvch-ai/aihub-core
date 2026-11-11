from typing import Any

import httpx
from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModConfiguration, OpenWebuiModHost, OpenWebuiModResolver,
    OpenWebuiModSelection, OpenWebuiModStore, OpenWebuiSettings,
)

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_global_state import OpenWebuiModGlobalState
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_publication_response import OpenWebuiModPublicationResponse
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService


class OpenWebuiModGlobalService:
    @staticmethod
    def _client() -> httpx.AsyncClient:
        settings = OpenWebuiSettings()
        return httpx.AsyncClient(
            base_url=settings.BASE_URL.rstrip("/") + "/_aihub/mods/control/", timeout=60,
            headers={"Authorization": f"Bearer {settings.SCIM_TOKEN.get_secret_value()}"},
        )

    @staticmethod
    async def _request(http: httpx.AsyncClient, method: str, path: str, content: bytes | None = None) -> httpx.Response:
        try:
            response = await http.request(method, path, content=content)
        except httpx.RequestError as error:
            raise HTTPException(503, "Open WebUI mod management is unavailable; reload after it recovers.") from error
        if response.is_error:
            detail = response.json().get("detail") if response.headers.get("content-type", "").startswith("application/json") else None
            raise HTTPException(response.status_code, detail or "Open WebUI refused the management operation.")
        return response

    @staticmethod
    def _state(response: httpx.Response) -> OpenWebuiModGlobalState:
        state = OpenWebuiModGlobalState.model_validate(response.json())
        for mod in state.configuration.mods:
            if mod.mod_id in OpenWebuiModBundles.packages():
                mod.publication = None
        return state

    @classmethod
    async def get(cls) -> OpenWebuiModGlobalState:
        async with cls._client() as http:
            return cls._state(await cls._request(http, "GET", "global"))

    @classmethod
    async def replace(cls, configuration: OpenWebuiModConfiguration, storage: S3Client) -> OpenWebuiModGlobalState:
        async with cls._client() as http:
            prepared = await cls._prepare(configuration, storage, http)
            response = await cls._request(http, "PUT", "global", prepared.model_dump_json().encode())
            return cls._state(response)

    @classmethod
    async def _prepare(
        cls, configuration: OpenWebuiModConfiguration, storage: S3Client, http: httpx.AsyncClient,
    ) -> OpenWebuiModConfiguration:
        host = await OpenWebuiModService.get_host()
        prepared = configuration.model_copy(deep=True)
        store = OpenWebuiModStore(storage)
        for mod in prepared.mods:
            publication = await cls._publication(mod, host)
            source = await OpenWebuiModService.get_revision(publication.manifest.source_revision)
            if publication.mod_id != mod.mod_id or source.manifest.backend is None:
                raise HTTPException(422, f"Select a backend publication belonging to '{mod.mod_id}'.")
            if not source.manifest.backend_overrides and not source.manifest.backend_restart_required:
                raise HTTPException(422, f"'{mod.mod_id}' needs declared callable overrides or an explicit backend restart requirement for global activation.")
            if mod.enabled and (publication.manifest.compatibility != host.compatibility or any(
                host.callables.get(target) != fingerprint for target, fingerprint in publication.manifest.backend_targets.items()
            )):
                raise HTTPException(409, f"Republish '{mod.mod_id}' for this Open WebUI host.")
            mod.publication = publication.revision
            for kind, revision, content in [
                ("sources", source.revision, await store.read_archive(source.revision)),
                ("publications", publication.revision, await store.read_publication(publication.revision)),
            ]:
                await cls._request(http, "PUT", f"archives/{kind}/{revision}", content)
        return prepared

    @staticmethod
    async def _publication(mod: OpenWebuiModSelection, host: OpenWebuiModHost) -> OpenWebuiModPublicationResponse:
        builtin = OpenWebuiModBundles.packages().get(mod.mod_id)
        if builtin is not None:
            if mod.publication is not None:
                raise HTTPException(422, f"Built-in '{mod.mod_id}' follows AI Hub and cannot be pinned.")
            publication = await OpenWebuiModResolver.publication(builtin.revision, host.compatibility)
            if publication is None:
                raise HTTPException(409, "Initialize supplied mods before global activation.")
            return OpenWebuiModPublicationResponse.from_entity(publication)
        if mod.publication is None:
            raise HTTPException(422, f"Select a published backend version of '{mod.mod_id}' first.")
        return await OpenWebuiModService.get_publication(mod.publication)

    @classmethod
    async def reconcile(cls, storage: S3Client) -> OpenWebuiModGlobalState:
        async with cls._client() as http:
            response = await cls._request(http, "GET", "global")
            current = OpenWebuiModGlobalState.model_validate(response.json())
            configuration = cls._state(response).configuration
            if not any(mod.mod_id in OpenWebuiModBundles.packages() for mod in configuration.mods):
                return cls._state(response)
            prepared = await cls._prepare(configuration, storage, http)
            if prepared != current.configuration:
                response = await cls._request(http, "PUT", "global", prepared.model_dump_json().encode())
            return cls._state(response)

    @classmethod
    async def restart(cls, version: int) -> dict[str, Any]:
        async with cls._client() as http:
            return (await cls._request(http, "POST", f"restart?version={version}")).json()
