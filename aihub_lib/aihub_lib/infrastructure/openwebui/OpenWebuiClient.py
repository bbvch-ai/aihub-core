"""Thin async wrapper around the OpenWebUI REST API."""

from typing import Any

import httpx

from aihub_lib.infrastructure.openwebui.OpenWebuiTokenService import OpenWebuiTokenService


class OpenWebuiClient:
    def __init__(self, base_url: str, secret_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret_key = secret_key

    @property
    def _headers(self) -> dict[str, str]:
        token = OpenWebuiTokenService.generate_token(self._secret_key)
        return {"Authorization": f"Bearer {token}"}

    async def list_groups(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/groups/", headers=self._headers)
        response.raise_for_status()
        return response.json()

    async def create_group(self, client: httpx.AsyncClient, name: str, description: str) -> dict[str, Any]:
        response = await client.post(
            f"{self._base_url}/api/v1/groups/create",
            headers=self._headers,
            json={"name": name, "description": description},
        )
        response.raise_for_status()
        return response.json()

    async def delete_group(self, client: httpx.AsyncClient, group_id: str) -> None:
        response = await client.delete(
            f"{self._base_url}/api/v1/groups/id/{group_id}/delete",
            headers=self._headers,
        )
        response.raise_for_status()

    async def get_group(self, client: httpx.AsyncClient, group_id: str) -> dict[str, Any]:
        response = await client.get(
            f"{self._base_url}/api/v1/groups/id/{group_id}",
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    async def update_group_members(self, client: httpx.AsyncClient, group_id: str, user_ids: list[str]) -> None:
        group = await self.get_group(client, group_id)
        current_members: list[str] = group.get("user_ids", [])

        desired = set(user_ids)
        current = set(current_members)

        to_add = desired - current
        to_remove = current - desired

        if to_add:
            response = await client.post(
                f"{self._base_url}/api/v1/groups/id/{group_id}/users/add",
                headers=self._headers,
                json={"user_ids": list(to_add)},
            )
            response.raise_for_status()

        if to_remove:
            response = await client.post(
                f"{self._base_url}/api/v1/groups/id/{group_id}/users/remove",
                headers=self._headers,
                json={"user_ids": list(to_remove)},
            )
            response.raise_for_status()

    async def list_models(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/models/list", headers=self._headers)
        response.raise_for_status()
        data = response.json()
        return data.get("items", []) if isinstance(data, dict) else data

    async def create_model(self, client: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        model_data.setdefault("params", {})
        response = await client.post(
            f"{self._base_url}/api/v1/models/create",
            headers=self._headers,
            json=model_data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_model(self, client: httpx.AsyncClient, model_id: str) -> None:
        response = await client.post(
            f"{self._base_url}/api/v1/models/model/delete",
            headers=self._headers,
            json={"id": model_id},
        )
        response.raise_for_status()

    async def get_model(self, client: httpx.AsyncClient, model_id: str) -> dict[str, Any]:
        response = await client.get(
            f"{self._base_url}/api/v1/models/model",
            headers=self._headers,
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
            headers=self._headers,
            json=form,
        )
        response.raise_for_status()
        return response.json()

    async def list_users(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/users/", headers=self._headers)
        response.raise_for_status()
        data = response.json()
        return data.get("users", []) if isinstance(data, dict) else data
