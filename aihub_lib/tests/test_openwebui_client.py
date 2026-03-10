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


def _error_response(status_code: int = 500) -> httpx.Response:
    return httpx.Response(status_code=status_code, request=httpx.Request("GET", f"{BASE_URL}/test"))


class TestListGroups:
    @pytest.mark.asyncio
    async def test_list_groups_sends_get_to_scim_endpoint(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(
            json_data={"Resources": [{"id": "g1", "displayName": "grp"}], "totalResults": 1}
        )

        result = await owui_client.list_groups(mock_client)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/v1/scim/v2/Groups" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"] == f"Bearer {SCIM_TOKEN}"
        assert call_args[1]["params"]["startIndex"] == 1
        assert result == [{"id": "g1", "displayName": "grp"}]

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


class TestCreateGroup:
    @pytest.mark.asyncio
    async def test_create_group_sends_post_to_scim(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201, {"id": "grp-1", "displayName": "test-group"})

        await owui_client.create_group(mock_client, "test-group", "A test group")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/scim/v2/Groups" in call_args[0][0]
        assert call_args[1]["json"]["displayName"] == "test-group"
        assert "schemas" in call_args[1]["json"]


class TestDeleteGroup:
    @pytest.mark.asyncio
    async def test_delete_group_sends_delete_to_scim(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.delete.return_value = _ok_response(204)

        await owui_client.delete_group(mock_client, "grp-123")

        mock_client.delete.assert_called_once()
        assert "/api/v1/scim/v2/Groups/grp-123" in mock_client.delete.call_args[0][0]


class TestUpdateGroupMembers:
    @pytest.mark.asyncio
    async def test_update_group_members_sends_put(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(
            json_data={"id": "grp-1", "displayName": "test-group", "members": []}
        )
        mock_client.put.return_value = _ok_response()

        await owui_client.update_group_members(mock_client, "grp-1", ["user-a", "user-b"])

        mock_client.get.assert_called_once()
        assert "/api/v1/scim/v2/Groups/grp-1" in mock_client.get.call_args[0][0]
        mock_client.put.assert_called_once()
        call_args = mock_client.put.call_args
        assert "/api/v1/scim/v2/Groups/grp-1" in call_args[0][0]
        members = call_args[1]["json"]["members"]
        assert {"value": "user-a"} in members
        assert {"value": "user-b"} in members


class TestListUsers:
    @pytest.mark.asyncio
    async def test_list_users_sends_get_to_scim(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(
            json_data={"Resources": [{"id": "u1", "userName": "alice@example.com"}], "totalResults": 1}
        )

        result = await owui_client.list_users(mock_client)

        mock_client.get.assert_called_once()
        assert "/api/v1/scim/v2/Users" in mock_client.get.call_args[0][0]
        assert result == [{"id": "u1", "userName": "alice@example.com"}]


class TestListModels:
    @pytest.mark.asyncio
    async def test_list_models_sends_get_with_jwt(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data=[])

        await owui_client.list_models(mock_client)

        mock_client.get.assert_called_once()
        assert "/api/v1/models/" in mock_client.get.call_args[0][0]
        assert mock_client.get.call_args[1]["headers"]["Authorization"].startswith("Bearer ey")


class TestCreateModel:
    @pytest.mark.asyncio
    async def test_create_model_sends_post_with_jwt(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201, {"id": "model-1"})
        model_data = {
            "id": "aihub-agent-rag-default",
            "name": "RAG Agent",
            "base_model_id": "aihub-pipeline.rag.default",
        }

        await owui_client.create_model(mock_client, model_data)

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/models/create" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"].startswith("Bearer ey")
        assert call_args[1]["json"] == model_data


class TestDeleteModel:
    @pytest.mark.asyncio
    async def test_delete_model_sends_post_with_jwt(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response()

        await owui_client.delete_model(mock_client, "aihub-agent-rag-default")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/models/model/delete" in call_args[0][0]
        assert call_args[1]["json"] == {"id": "aihub-agent-rag-default"}


class TestUpdateModelAccess:
    @pytest.mark.asyncio
    async def test_update_model_access_sends_post_with_jwt(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        model_data = {"id": "aihub-agent-rag-default", "name": "RAG Agent", "meta": {}, "params": {}}
        mock_client.get.return_value = _ok_response(json_data=model_data)
        mock_client.post.return_value = _ok_response()
        access_grants = [
            {"principal_type": "group", "principal_id": "grp-1", "permission": "read"},
            {"principal_type": "group", "principal_id": "grp-2", "permission": "read"},
        ]

        await owui_client.update_model_access(mock_client, "aihub-agent-rag-default", access_grants)

        mock_client.get.assert_called_once()
        assert "/api/v1/models/model" in mock_client.get.call_args[0][0]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/models/model/update" in call_args[0][0]
        assert call_args[1]["json"]["access_grants"] == access_grants
        assert call_args[1]["json"]["id"] == "aihub-agent-rag-default"


class TestAuthHeaders:
    @pytest.mark.asyncio
    async def test_scim_methods_use_scim_token(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data={"Resources": [], "totalResults": 0})
        mock_client.post.return_value = _ok_response(201, {})
        mock_client.delete.return_value = _ok_response(204)

        await owui_client.list_groups(mock_client)
        await owui_client.list_users(mock_client)

        for call in mock_client.get.call_args_list:
            assert call[1]["headers"]["Authorization"] == f"Bearer {SCIM_TOKEN}"

    @pytest.mark.asyncio
    async def test_model_methods_use_jwt_token(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        model_data = {"id": "m", "name": "M", "meta": {}, "params": {}}
        mock_client.get.return_value = _ok_response(json_data=model_data)
        mock_client.post.return_value = _ok_response(201, {})

        await owui_client.list_models(mock_client)
        await owui_client.create_model(mock_client, {})
        await owui_client.update_model_access(mock_client, "m", [])

        for call in mock_client.get.call_args_list:
            assert call[1]["headers"]["Authorization"].startswith("Bearer ey")
        for call in mock_client.post.call_args_list:
            assert call[1]["headers"]["Authorization"].startswith("Bearer ey")

    @pytest.mark.asyncio
    async def test_http_error_propagates(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _error_response(500)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.list_groups(mock_client)
