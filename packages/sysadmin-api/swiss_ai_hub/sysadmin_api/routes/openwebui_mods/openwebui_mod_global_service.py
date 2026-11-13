from typing import Any

import httpx
from fastapi import HTTPException
from mypy_boto3_s3 import S3Client
from starlette.concurrency import run_in_threadpool
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModActivation, OpenWebuiModConfiguration, OpenWebuiModHost, OpenWebuiModPublicationManifest,
    OpenWebuiModResolvedConfiguration, OpenWebuiModSelection, OpenWebuiModStore, OpenWebuiSettings,
)

from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.dto.openwebui_mod_global_state import OpenWebuiModGlobalState
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
        data = response.json()
        for mod in data["configuration"]["mods"]:
            mod.pop("publication")
        return OpenWebuiModGlobalState.model_validate(data)

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
    ) -> OpenWebuiModResolvedConfiguration:
        host = await OpenWebuiModService.get_host()
        return OpenWebuiModResolvedConfiguration(
            version=configuration.version,
            mods=[await cls._stage(mod, host, storage, http) for mod in configuration.mods],
        )

    @classmethod
    async def _stage(
        cls, mod: OpenWebuiModSelection, host: OpenWebuiModHost, storage: S3Client, http: httpx.AsyncClient,
    ) -> OpenWebuiModActivation:
        installed = await run_in_threadpool(OpenWebuiModEntity.find_mod, mod.mod_id)
        if installed is None:
            raise HTTPException(422, f"Unknown mod '{mod.mod_id}'.")
        publication = OpenWebuiModPublicationManifest.model_validate_json(installed.publication_manifest_json)
        if mod.enabled and (publication.compatibility != host.compatibility or any(
            host.callables.get(target) != fingerprint for target, fingerprint in publication.backend_targets.items()
        )):
            raise HTTPException(409, f"Reinstall '{mod.mod_id}' for this Open WebUI host.")
        store = OpenWebuiModStore(storage)
        for kind, revision, content in [
            ("sources", installed.source_revision, await store.read_archive(installed.source_revision)),
            ("publications", installed.publication, await store.read_publication(installed.publication)),
        ]:
            await cls._request(http, "PUT", f"archives/{kind}/{revision}", content)
        return OpenWebuiModActivation(**mod.model_dump(), publication=installed.publication)

    @classmethod
    async def reconcile(cls, storage: S3Client, *, mod_id: str | None = None) -> OpenWebuiModGlobalState:
        async with cls._client() as http:
            response = await cls._request(http, "GET", "global")
            current = OpenWebuiModResolvedConfiguration.model_validate(response.json()["configuration"])
            state = cls._state(response)
            if not any(mod_id is None or mod.mod_id == mod_id for mod in state.configuration.mods):
                return state
            host = await OpenWebuiModService.get_host()
            prepared = current.model_copy(deep=True)
            for index, mod in enumerate(state.configuration.mods):
                if mod_id is None or mod.mod_id == mod_id:
                    prepared.mods[index] = await cls._stage(mod, host, storage, http)
            if prepared != current:
                response = await cls._request(http, "PUT", "global", prepared.model_dump_json().encode())
                return cls._state(response)
            return state

    @classmethod
    async def restart(cls, version: int) -> dict[str, Any]:
        async with cls._client() as http:
            return (await cls._request(http, "POST", f"restart?version={version}")).json()
