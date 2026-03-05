"""Thin async wrapper around the OpenWebUI REST API."""

from typing import Any

import httpx


class OpenWebuiClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

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

    async def update_group_members(
        self, client: httpx.AsyncClient, group_id: str, user_ids: list[str]
    ) -> dict[str, Any]:
        response = await client.post(
            f"{self._base_url}/api/v1/groups/id/{group_id}/update",
            headers=self._headers,
            json={"user_ids": user_ids},
        )
        response.raise_for_status()
        return response.json()

    async def list_models(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/models/", headers=self._headers)
        response.raise_for_status()
        return response.json()

    async def create_model(self, client: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        response = await client.post(
            f"{self._base_url}/api/v1/models/create",
            headers=self._headers,
            json=model_data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_model(self, client: httpx.AsyncClient, model_id: str) -> None:
        response = await client.delete(
            f"{self._base_url}/api/v1/models/delete",
            headers=self._headers,
            params={"id": model_id},
        )
        response.raise_for_status()

    async def update_model_access(
        self, client: httpx.AsyncClient, model_id: str, access_control: dict[str, Any]
    ) -> dict[str, Any]:
        response = await client.post(
            f"{self._base_url}/api/v1/models/update",
            headers=self._headers,
            params={"id": model_id},
            json={"access_control": access_control},
        )
        response.raise_for_status()
        return response.json()

    async def list_users(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await client.get(f"{self._base_url}/api/v1/users/", headers=self._headers)
        response.raise_for_status()
        return response.json()
