"""Thin async wrapper around the OpenWebUI REST API."""

from typing import Any

import httpx

from aihub_lib.infrastructure.openwebui.OpenWebuiTokenService import OpenWebuiTokenService

SCIM_SCHEMAS_GROUP = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
SCIM_PAGE_SIZE = 100


class OpenWebuiClient:
    def __init__(self, base_url: str, secret_key: str, scim_token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret_key = secret_key
        self._scim_token = scim_token

    @property
    def _scim_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._scim_token}", "Content-Type": "application/scim+json"}

    @property
    def _jwt_headers(self) -> dict[str, str]:
        token = OpenWebuiTokenService.generate_token(self._secret_key)
        return {"Authorization": f"Bearer {token}"}

    async def _list_scim_resources(self, client: httpx.AsyncClient, endpoint: str) -> list[dict[str, Any]]:
        """Fetches all resources from a SCIM 2.0 list endpoint, handling pagination."""
        all_resources: list[dict[str, Any]] = []
        start_index = 1

        while True:
            response = await client.get(
                f"{self._base_url}{endpoint}",
                headers=self._scim_headers,
                params={"startIndex": start_index, "count": SCIM_PAGE_SIZE},
            )
            response.raise_for_status()
            data = response.json()
            resources = data.get("Resources", [])
            all_resources.extend(resources)

            total = data.get("totalResults", 0)
            if start_index + len(resources) > total or not resources:
                break
            start_index += len(resources)

        return all_resources

    # ------------------------------------------------------------------
    # Group methods (SCIM 2.0)
    # ------------------------------------------------------------------

    async def list_groups(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        return await self._list_scim_resources(client, "/api/v1/scim/v2/Groups")

    async def create_group(self, client: httpx.AsyncClient, name: str, description: str) -> dict[str, Any]:
        response = await client.post(
            f"{self._base_url}/api/v1/scim/v2/Groups",
            headers=self._scim_headers,
            json={"schemas": SCIM_SCHEMAS_GROUP, "displayName": name},
        )
        response.raise_for_status()
        return response.json()

    async def delete_group(self, client: httpx.AsyncClient, group_id: str) -> None:
        response = await client.delete(
            f"{self._base_url}/api/v1/scim/v2/Groups/{group_id}",
            headers=self._scim_headers,
        )
        response.raise_for_status()

    async def get_group(self, client: httpx.AsyncClient, group_id: str) -> dict[str, Any]:
        response = await client.get(
            f"{self._base_url}/api/v1/scim/v2/Groups/{group_id}",
            headers=self._scim_headers,
        )
        response.raise_for_status()
        return response.json()

    async def update_group_members(self, client: httpx.AsyncClient, group_id: str, user_ids: list[str]) -> None:
        group = await self.get_group(client, group_id)
        members = [{"value": uid} for uid in user_ids]
        response = await client.put(
            f"{self._base_url}/api/v1/scim/v2/Groups/{group_id}",
            headers=self._scim_headers,
            json={
                "schemas": SCIM_SCHEMAS_GROUP,
                "displayName": group["displayName"],
                "members": members,
            },
        )
        response.raise_for_status()

    # ------------------------------------------------------------------
    # User methods (SCIM 2.0)
    # ------------------------------------------------------------------

    async def list_users(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        return await self._list_scim_resources(client, "/api/v1/scim/v2/Users")

    # ------------------------------------------------------------------
    # Model methods (proprietary API + JWT auth)
    # ------------------------------------------------------------------

    async def list_models(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/models/list", headers=self._jwt_headers)
        response.raise_for_status()
        data = response.json()
        return data.get("items", []) if isinstance(data, dict) else data

    async def create_model(self, client: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        model_data.setdefault("params", {})
        response = await client.post(
            f"{self._base_url}/api/v1/models/create",
            headers=self._jwt_headers,
            json=model_data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_model(self, client: httpx.AsyncClient, model_id: str) -> None:
        response = await client.post(
            f"{self._base_url}/api/v1/models/model/delete",
            headers=self._jwt_headers,
            json={"id": model_id},
        )
        response.raise_for_status()

    async def get_model(self, client: httpx.AsyncClient, model_id: str) -> dict[str, Any]:
        response = await client.get(
            f"{self._base_url}/api/v1/models/model",
            headers=self._jwt_headers,
            params={"id": model_id},
        )
        response.raise_for_status()
        return response.json()

    async def update_model_access(
        self, client: httpx.AsyncClient, model_id: str, access_control: dict[str, Any]
    ) -> dict[str, Any]:
        model = await self.get_model(client, model_id)
        form = {
            "id": model["id"],
            "name": model["name"],
            "meta": model.get("meta", {}),
            "params": model.get("params", {}),
            "access_control": access_control or None,
        }
        if model.get("base_model_id"):
            form["base_model_id"] = model["base_model_id"]
        response = await client.post(
            f"{self._base_url}/api/v1/models/model/update",
            headers=self._jwt_headers,
            json=form,
        )
        response.raise_for_status()
        return response.json()
