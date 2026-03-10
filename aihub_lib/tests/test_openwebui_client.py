"""Tests for OpenWebuiClient — thin async wrapper around OpenWebUI REST API."""

from unittest.mock import AsyncMock

import httpx
import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiClient import OpenWebuiClient

BASE_URL = "http://open-webui:8080"
SECRET_KEY = "test-secret-key-for-jwt-signing"
SCIM_TOKEN = "test-scim-token"


@pytest.fixture
def owui_client() -> OpenWebuiClient:
    return OpenWebuiClient(base_url=BASE_URL, secret_key=SECRET_KEY, scim_token=SCIM_TOKEN)


def _ok_response(status_code: int = 200, json_data: dict | list | None = None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data if json_data is not None else {},
        request=httpx.Request("GET", f"{BASE_URL}/test"),
    )


class TestListGroups:
    @pytest.mark.asyncio
    async def test_list_groups_paginates_through_all_pages(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        page1 = _ok_response(json_data={"Resources": [{"id": f"g{i}"} for i in range(100)], "totalResults": 150})
        page2 = _ok_response(json_data={"Resources": [{"id": f"g{i}"} for i in range(100, 150)], "totalResults": 150})
        mock_client.get.side_effect = [page1, page2]

        result = await owui_client.list_groups(mock_client)

        assert len(result) == 150
        assert mock_client.get.call_count == 2
        assert mock_client.get.call_args_list[1][1]["params"]["startIndex"] == 101
