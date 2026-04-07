from unittest.mock import AsyncMock

import httpx
import pytest

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import OpenWebuiClient

BASE_URL = "http://open-webui:8080"
SECRET_KEY = "test-secret-key-for-jwt-signing"
SERVICE_ACCOUNT_ID = "00000000-0000-4000-a000-000000000001"


@pytest.fixture
def owui_client() -> OpenWebuiClient:
    return OpenWebuiClient(
        base_url=BASE_URL,
        secret_key=SECRET_KEY,
        service_account_id=SERVICE_ACCOUNT_ID,
    )


def _response(status_code: int = 200, json_data: dict | list | None = None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data if json_data is not None else {},
        request=httpx.Request("GET", f"{BASE_URL}/test"),
    )


class TestListModels:
    @pytest.mark.asyncio
    async def test_list_models_handles_dict_response_with_items(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(json_data={"items": [{"id": "m1"}]})

        result = await owui_client.list_models(mock_client)

        assert result == [{"id": "m1"}]

    @pytest.mark.asyncio
    async def test_list_models_handles_bare_list_response(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(json_data=[{"id": "m1"}])

        result = await owui_client.list_models(mock_client)

        assert result == [{"id": "m1"}]


class TestErrorPropagation:
    @pytest.mark.asyncio
    async def test_list_models_raises_on_server_error(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.list_models(mock_client)

    @pytest.mark.asyncio
    async def test_create_model_raises_on_validation_error(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(status_code=422)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.create_model(mock_client, {"id": "test"})

    @pytest.mark.asyncio
    async def test_delete_model_raises_on_not_found(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(status_code=404)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.delete_model(mock_client, "nonexistent")
