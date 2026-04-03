import logging
from typing import Any

import httpx

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_token_service import OpenWebuiTokenService

logger = logging.getLogger(__name__)

MODELS_ENDPOINT = "/api/v1/models"


class OpenWebuiClient:
    def __init__(self, base_url: str, secret_key: str, service_account_id: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._secret_key = secret_key
        self._service_account_id = service_account_id

    @property
    def _jwt_headers(self) -> dict[str, str]:
        token = OpenWebuiTokenService.generate_token(self._secret_key, user_id=self._service_account_id)
        return {"Authorization": f"Bearer {token}"}

    async def list_models(self, http: httpx.AsyncClient) -> list[dict[str, Any]]:
        response = await http.get(f"{self._base_url}{MODELS_ENDPOINT}/list", headers=self._jwt_headers)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            if "items" not in data:
                logger.warning("OpenWebUI list_models returned dict without 'items' key: %s", list(data.keys()))
            return data.get("items", [])
        return data

    async def create_model(self, http: httpx.AsyncClient, model_data: dict[str, Any]) -> dict[str, Any]:
        model_data.setdefault("params", {})
        response = await http.post(
            f"{self._base_url}{MODELS_ENDPOINT}/create",
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
