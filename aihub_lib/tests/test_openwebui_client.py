"""Tests for OpenWebuiClient — thin async wrapper around OpenWebUI REST API."""

from unittest.mock import AsyncMock

import httpx
import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiClient import OpenWebuiClient

BASE_URL = "http://open-webui:8080"
SECRET_KEY = "test-secret-key-for-jwt-signing"


@pytest.fixture
def owui_client() -> OpenWebuiClient:
    return OpenWebuiClient(base_url=BASE_URL, secret_key=SECRET_KEY)


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
    async def test_list_groups_sends_get_with_auth(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data=[])

        await owui_client.list_groups(mock_client)

        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/v1/groups/" in call_args[0][0]
        assert call_args[1]["headers"]["Authorization"].startswith("Bearer ey")


class TestCreateGroup:
    @pytest.mark.asyncio
    async def test_create_group_sends_post(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response(201, {"id": "grp-1"})

        await owui_client.create_group(mock_client, "test-group", "A test group")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/groups/create" in call_args[0][0]
        assert call_args[1]["json"] == {"name": "test-group", "description": "A test group"}


class TestDeleteGroup:
    @pytest.mark.asyncio
    async def test_delete_group_sends_delete(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.delete.return_value = _ok_response()

        await owui_client.delete_group(mock_client, "grp-123")

        mock_client.delete.assert_called_once()
        assert "/api/v1/groups/id/grp-123/delete" in mock_client.delete.call_args[0][0]


class TestUpdateGroupMembers:
    @pytest.mark.asyncio
    async def test_update_group_members_adds_new_users(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data={"id": "grp-1", "user_ids": []})
        mock_client.post.return_value = _ok_response()

        await owui_client.update_group_members(mock_client, "grp-1", ["user-a", "user-b"])

        mock_client.get.assert_called_once()
        assert "/api/v1/groups/id/grp-1" in mock_client.get.call_args[0][0]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/groups/id/grp-1/users/add" in call_args[0][0]
        assert set(call_args[1]["json"]["user_ids"]) == {"user-a", "user-b"}


class TestListModels:
    @pytest.mark.asyncio
    async def test_list_models_sends_get(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data=[])

        await owui_client.list_models(mock_client)

        mock_client.get.assert_called_once()
        assert "/api/v1/models/" in mock_client.get.call_args[0][0]


class TestCreateModel:
    @pytest.mark.asyncio
    async def test_create_model_sends_post(self, owui_client: OpenWebuiClient) -> None:
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
        assert call_args[1]["json"] == model_data


class TestDeleteModel:
    @pytest.mark.asyncio
    async def test_delete_model_sends_post(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _ok_response()

        await owui_client.delete_model(mock_client, "aihub-agent-rag-default")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/models/model/delete" in call_args[0][0]
        assert call_args[1]["json"] == {"id": "aihub-agent-rag-default"}


class TestUpdateModelAccess:
    @pytest.mark.asyncio
    async def test_update_model_access_sends_post(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        model_data = {"id": "aihub-agent-rag-default", "name": "RAG Agent", "meta": {}, "params": {}}
        mock_client.get.return_value = _ok_response(json_data=model_data)
        mock_client.post.return_value = _ok_response()
        access_control = {"read": {"group_ids": ["grp-1", "grp-2"]}}

        await owui_client.update_model_access(mock_client, "aihub-agent-rag-default", access_control)

        mock_client.get.assert_called_once()
        assert "/api/v1/models/model" in mock_client.get.call_args[0][0]
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "/api/v1/models/model/update" in call_args[0][0]
        assert call_args[1]["json"]["access_control"] == access_control
        assert call_args[1]["json"]["id"] == "aihub-agent-rag-default"


class TestListUsers:
    @pytest.mark.asyncio
    async def test_list_users_sends_get(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _ok_response(json_data=[])

        await owui_client.list_users(mock_client)

        mock_client.get.assert_called_once()
        assert "/api/v1/users/" in mock_client.get.call_args[0][0]


class TestAuthAndErrors:
    @pytest.mark.asyncio
    async def test_all_methods_include_bearer_token(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        model_data = {"id": "m", "name": "M", "meta": {}, "params": {}}
        group_data = {"id": "g", "name": "g", "user_ids": []}
        mock_client.get.return_value = _ok_response(json_data=model_data)
        mock_client.post.return_value = _ok_response(201, {})
        mock_client.delete.return_value = _ok_response()

        await owui_client.list_groups(mock_client)
        await owui_client.list_models(mock_client)
        await owui_client.list_users(mock_client)
        await owui_client.create_group(mock_client, "g", "d")
        await owui_client.create_model(mock_client, {})

        # get_model returns model_data, then update_model_access posts
        await owui_client.update_model_access(mock_client, "m", {})

        # get_group returns group_data for update_group_members
        mock_client.get.return_value = _ok_response(json_data=group_data)
        await owui_client.update_group_members(mock_client, "g", [])

        await owui_client.delete_group(mock_client, "g")
        await owui_client.delete_model(mock_client, "m")

        for call in mock_client.get.call_args_list:
            assert call[1]["headers"]["Authorization"].startswith("Bearer ey")
        for call in mock_client.post.call_args_list:
            assert call[1]["headers"]["Authorization"].startswith("Bearer ey")
        for call in mock_client.delete.call_args_list:
            assert call[1]["headers"]["Authorization"].startswith("Bearer ey")

    @pytest.mark.asyncio
    async def test_http_error_propagates(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _error_response(500)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.list_groups(mock_client)
