from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from scim2_models import Group, User

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_client import SCIM_PAGE_SIZE, OpenWebuiClient

BASE_URL = "http://open-webui:8080"
SECRET_KEY = "test-secret-key-for-jwt-signing"
SERVICE_ACCOUNT_ID = "00000000-0000-4000-a000-000000000001"


SCIM_TOKEN = "test-scim-token"


@pytest.fixture
def owui_client() -> OpenWebuiClient:
    return OpenWebuiClient(
        base_url=BASE_URL,
        secret_key=SECRET_KEY,
        scim_token=SCIM_TOKEN,
        service_account_id=SERVICE_ACCOUNT_ID,
    )


def _response(status_code: int = 200, json_data: dict | list | None = None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data if json_data is not None else {},
        request=httpx.Request("GET", f"{BASE_URL}/test"),
    )


class TestUpdateModelAccess:
    @pytest.mark.asyncio
    async def test_clears_access_when_no_grants(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(
            json_data={"id": "m1", "name": "Model 1", "meta": {}, "params": {}, "base_model_id": "base-1"}
        )
        mock_client.post.return_value = _response(json_data={"id": "m1"})

        result = await owui_client.update_model_access(mock_client, "m1", [])
        assert result == {"id": "m1"}

        call_args = mock_client.post.call_args
        assert call_args.kwargs["json"]["access_grants"] is None


class TestUpdateModel:
    @pytest.mark.asyncio
    async def test_posts_model_data_to_update_endpoint(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(json_data={"id": "m1", "name": "New Name"})

        result = await owui_client.update_model(mock_client, {"id": "m1", "name": "New Name"})
        assert result == {"id": "m1", "name": "New Name"}

        call_args = mock_client.post.call_args
        assert call_args.args[0].endswith("/api/v1/models/model/update")
        assert call_args.kwargs["json"]["name"] == "New Name"
        assert call_args.kwargs["json"]["params"] == {}

    @pytest.mark.asyncio
    async def test_raises_on_server_error(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.update_model(mock_client, {"id": "m1", "name": "New Name"})


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


def _scim_group(display_name: str, group_id: str) -> Group:
    group = Group(display_name=display_name)
    group.id = group_id
    return group


class TestCreateGroupIdempotent:
    @pytest.mark.asyncio
    async def test_reuses_existing_group_with_same_name(self, owui_client: OpenWebuiClient) -> None:
        existing = _scim_group("aihub:T:R", "grp-existing")
        scim = AsyncMock()
        scim.query.return_value = SimpleNamespace(resources=[existing], total_results=1)

        result = await owui_client.create_group("aihub:T:R", scim=scim)

        assert result is existing
        scim.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_when_no_group_with_that_name_exists(self, owui_client: OpenWebuiClient) -> None:
        created = _scim_group("aihub:T:R", "grp-new")
        scim = AsyncMock()
        scim.query.return_value = SimpleNamespace(
            resources=[_scim_group("aihub:Other:Role", "grp-other")], total_results=1
        )
        scim.create.return_value = created

        result = await owui_client.create_group("aihub:T:R", scim=scim)

        assert result is created
        scim.create.assert_awaited_once()


class TestScimPagination:
    @pytest.mark.asyncio
    async def test_list_users_follows_all_pages(self, owui_client: OpenWebuiClient) -> None:
        total = SCIM_PAGE_SIZE + 25  # spans two pages
        page1 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE)]
        page2 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE, total)]
        scim = AsyncMock()

        async def fake_query(model: type, search_request=None, **kwargs):  # noqa: ANN001
            resources = page1 if search_request.start_index == 1 else page2
            return SimpleNamespace(resources=resources, total_results=total)

        scim.query.side_effect = fake_query

        result = await owui_client.list_users(scim=scim)

        assert len(result) == total
        assert scim.query.await_count == 2

    @pytest.mark.asyncio
    async def test_list_groups_stops_on_short_page(self, owui_client: OpenWebuiClient) -> None:
        scim = AsyncMock()
        scim.query.return_value = SimpleNamespace(resources=[_scim_group("aihub:T:R", "g1")], total_results=1)

        result = await owui_client.list_groups(scim=scim)

        assert len(result) == 1
        assert scim.query.await_count == 1
