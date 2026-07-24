import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
from scim2_client.engines.httpx import AsyncSCIMClient
from scim2_models import Group, GroupMember, ListResponse, Resource, SearchRequest, User

from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

logger = logging.getLogger(__name__)

SCIM_BASE_PATH = "/api/v1/scim/v2"
MODELS_ENDPOINT = "/api/v1/models"

# SCIM list endpoints are paginated; OpenWebUI defaults to a small page size, so a
# bare query returns only the first page. Request this many per page (the server may
# still cap it lower — pagination keys off the response, not this value).
SCIM_PAGE_SIZE = 100

# Backstop so a server that ignores startIndex can't spin the provisioner forever.
MAX_SCIM_PAGES = 10_000


class OpenWebuiClient:
    def __init__(self, base_url: str, secret_key: str, scim_token: str, service_account_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret_key = secret_key
        self._scim_token = scim_token
        self._service_account_id = service_account_id

    @asynccontextmanager
    async def scim_session(self) -> AsyncIterator[AsyncSCIMClient]:
        async with httpx.AsyncClient(
            base_url=f"{self._base_url}{SCIM_BASE_PATH}",
            headers={"Authorization": f"Bearer {self._scim_token}"},
            timeout=30.0,
        ) as http:
            scim = AsyncSCIMClient(
                http,
                resource_models=[Group, User],
                check_response_payload=True,
                check_response_content_type=True,
            )
            scim.register_naive_resource_types()
            yield scim

    @property
    def _jwt_headers(self) -> dict[str, str]:
        token = OpenWebuiTokenService.generate_token(self._secret_key, user_id=self._service_account_id)
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    async def _query_all[R: Resource](client: AsyncSCIMClient, model: type[R]) -> list[R]:
        """Returns every resource of ``model``, following SCIM pagination.

        ``client.query(model)`` returns a single page, and OpenWebUI's SCIM default
        page size is small — so a bare query silently drops every resource past the
        first page (e.g. users/groups never get synced once the directory grows).
        Loop on ``startIndex`` until every resource is retrieved.

        Termination keys off the server's reported ``itemsPerPage``/``totalResults``,
        not our requested ``count``: the server may cap the page size below what we
        ask, so ``len(batch) < SCIM_PAGE_SIZE`` would stop early and drop the rest.
        """
        results: list[R] = []
        start = 1
        for _ in range(MAX_SCIM_PAGES):
            response = cast(
                ListResponse[R],
                await client.query(model, search_request=SearchRequest(start_index=start, count=SCIM_PAGE_SIZE)),
            )
            batch = list(response.resources or [])
            results.extend(batch)
            total = response.total_results
            if total is not None and len(results) >= total:
                break
            # Server-reported page size — fall back to the batch length if absent.
            page_size = response.items_per_page or len(batch)
            if not batch or len(batch) < page_size:
                break
            start += len(batch)
        else:
            raise RuntimeError(f"SCIM pagination for {model.__name__} exceeded {MAX_SCIM_PAGES} pages")
        return results

    # ------------------------------------------------------------------
    # Group methods (SCIM 2.0 via scim2-client)
    # ------------------------------------------------------------------

    async def list_groups(self, scim: AsyncSCIMClient | None = None) -> list[Group]:
        if scim:
            return await self._query_all(scim, Group)
        async with self.scim_session() as s:
            return await self._query_all(s, Group)

    async def create_group(self, name: str, scim: AsyncSCIMClient | None = None) -> Group:
        """Creates a group, or returns the existing one if a group with this display name already exists.

        OpenWebUI/SCIM does not enforce unique display names, so a blind create can produce duplicate
        same-named groups (which breaks role-to-group sync). This makes creation idempotent.
        """

        async def _create(client: AsyncSCIMClient) -> Group:
            for group in await self._query_all(client, Group):
                if group.display_name == name:
                    logger.warning(
                        "OpenWebUI group '%s' already exists (id=%s); reusing it instead of creating a duplicate",
                        name,
                        group.id,
                    )
                    return group
            return await client.create(Group(display_name=name))

        if scim:
            return await _create(scim)
        async with self.scim_session() as s:
            return await _create(s)

    async def delete_group(self, group_id: str, scim: AsyncSCIMClient | None = None) -> None:
        if scim:
            await scim.delete(Group, group_id)
            return
        async with self.scim_session() as s:
            await s.delete(Group, group_id)

    async def update_group_members(
        self, group_id: str, user_ids: list[str], scim: AsyncSCIMClient | None = None
    ) -> None:
        async def _update(client: AsyncSCIMClient) -> None:
            group = await client.query(Group, id=group_id)
            group.members = [GroupMember(value=uid) for uid in user_ids]
            await client.replace(group)

        if scim:
            await _update(scim)
        else:
            async with self.scim_session() as s:
                await _update(s)

    # ------------------------------------------------------------------
    # User methods (SCIM 2.0 via scim2-client)
    # ------------------------------------------------------------------

    async def list_users(self, scim: AsyncSCIMClient | None = None) -> list[User]:
        if scim:
            return await self._query_all(scim, User)
        async with self.scim_session() as s:
            return await self._query_all(s, User)

    # ------------------------------------------------------------------
    # Model methods (proprietary API + JWT auth)
    # ------------------------------------------------------------------

    async def list_models(self, http: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await http.get(f"{self._base_url}{MODELS_ENDPOINT}/list", headers=self._jwt_headers)
        response.raise_for_status()
        data = response.json()
        return data.get("items", []) if isinstance(data, dict) else data

    async def list_base_models(self, http: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Lists registry entries that override a raw provider model (``base_model_id`` unset).

        ``list_models`` cannot see these: OpenWebUI's search filters on ``base_model_id != None``, so
        base-model overrides are invisible to it — and to the workspace UI that renders it.
        """
        response = await http.get(f"{self._base_url}{MODELS_ENDPOINT}/base", headers=self._jwt_headers)
        response.raise_for_status()
        return response.json()

    async def create_model(self, http: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        model_data.setdefault("params", {})
        response = await http.post(
            f"{self._base_url}{MODELS_ENDPOINT}/create",
            headers=self._jwt_headers,
            json=model_data,
        )
        response.raise_for_status()
        return response.json()

    async def update_model(self, http: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        model_data.setdefault("params", {})
        response = await http.post(
            f"{self._base_url}{MODELS_ENDPOINT}/model/update",
            headers=self._jwt_headers,
            json=model_data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_model(self, http: httpx.AsyncClient, model_id: str) -> None:
        response = await http.post(
            f"{self._base_url}{MODELS_ENDPOINT}/model/delete",
            headers=self._jwt_headers,
            json={"id": model_id},
        )
        response.raise_for_status()

    async def get_model(self, http: httpx.AsyncClient, model_id: str) -> dict[str, Any]:
        response = await http.get(
            f"{self._base_url}{MODELS_ENDPOINT}/model",
            headers=self._jwt_headers,
            params={"id": model_id},
        )
        response.raise_for_status()
        return response.json()

    async def update_model_access(
        self,
        http: httpx.AsyncClient,
        model_id: str,
        access_grants: list[AccessGrant],
    ) -> dict[str, Any]:
        model = await self.get_model(http, model_id)
        form = {
            "id": model["id"],
            "name": model["name"],
            "meta": model.get("meta", {}),
            "params": model.get("params", {}),
            "access_grants": [g.model_dump() for g in access_grants] if access_grants else None,
        }
        if model.get("base_model_id"):
            form["base_model_id"] = model["base_model_id"]
        response = await http.post(
            f"{self._base_url}{MODELS_ENDPOINT}/model/update",
            headers=self._jwt_headers,
            json=form,
        )
        response.raise_for_status()
        return response.json()
