import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from scim2_client.engines.httpx import AsyncSCIMClient
from scim2_models import Group, GroupMember, User

from swiss_ai_hub.core.infrastructure.openwebui.access_grant import AccessGrant
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

logger = logging.getLogger(__name__)

SCIM_BASE_PATH = "/api/v1/scim/v2"
MODELS_ENDPOINT = "/api/v1/models"


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

    # ------------------------------------------------------------------
    # Group methods (SCIM 2.0 via scim2-client)
    # ------------------------------------------------------------------

    async def list_groups(self, scim: AsyncSCIMClient | None = None) -> list[Group]:
        if scim:
            response = await scim.query(Group)
            return list(response.resources)
        async with self.scim_session() as s:
            response = await s.query(Group)
            return list(response.resources)

    async def create_group(self, name: str, scim: AsyncSCIMClient | None = None) -> Group:
        """Creates a group, or returns the existing one if a group with this display name already exists.

        OpenWebUI/SCIM does not enforce unique display names, so a blind create can produce duplicate
        same-named groups (which breaks role-to-group sync). This makes creation idempotent.
        """

        async def _create(client: AsyncSCIMClient) -> Group:
            response = await client.query(Group)
            for group in response.resources:
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
            response = await scim.query(User)
            return list(response.resources)
        async with self.scim_session() as s:
            response = await s.query(User)
            return list(response.resources)

    # ------------------------------------------------------------------
    # Model methods (proprietary API + JWT auth)
    # ------------------------------------------------------------------

    async def list_models(self, http: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await http.get(f"{self._base_url}{MODELS_ENDPOINT}/list", headers=self._jwt_headers)
        response.raise_for_status()
        data = response.json()
        return data.get("items", []) if isinstance(data, dict) else data

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
