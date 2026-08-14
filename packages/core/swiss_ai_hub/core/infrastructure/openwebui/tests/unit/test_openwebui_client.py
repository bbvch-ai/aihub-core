from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
from scim2_models import Group, User

import swiss_ai_hub.core.infrastructure.openwebui.openwebui_client as openwebui_client_module
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


def _model_pages(pages: list[list[dict]], *, total: int | None = -1) -> list[httpx.Response]:
    """One paginated ``/models/list`` response per page; ``total`` defaults to the overall count,
    pass ``None`` to simulate a server that omits it."""
    overall = sum(len(p) for p in pages)
    return [_response(json_data={"items": page, "total": overall if total == -1 else total}) for page in pages]


class TestListModels:
    @pytest.mark.asyncio
    async def test_single_page_below_cap_needs_one_request(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = _model_pages([[{"id": f"m{i}"} for i in range(6)]])

        result = await owui_client.list_models(mock_client)

        assert len(result) == 6
        assert mock_client.get.await_count == 1

    @pytest.mark.asyncio
    async def test_follows_all_pages(self, owui_client: OpenWebuiClient) -> None:
        pages = [
            [{"id": f"m{i}"} for i in range(30)],
            [{"id": f"m{i}"} for i in range(30, 60)],
            [{"id": f"m{i}"} for i in range(60, 65)],
        ]
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = _model_pages(pages)

        result = await owui_client.list_models(mock_client)

        assert [m["id"] for m in result] == [f"m{i}" for i in range(65)]
        assert mock_client.get.await_count == 3
        for call, expected_page in zip(mock_client.get.await_args_list, (1, 2, 3), strict=True):
            params = call.kwargs["params"]
            assert params["page"] == expected_page
            assert params["order_by"] == "created_at"
            assert params["direction"] == "desc"

    @pytest.mark.asyncio
    async def test_stops_at_exact_page_multiple(self, owui_client: OpenWebuiClient) -> None:
        pages = [[{"id": f"m{i}"} for i in range(30)], [{"id": f"m{i}"} for i in range(30, 60)]]
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = _model_pages(pages)

        result = await owui_client.list_models(mock_client)

        assert len(result) == 60
        assert mock_client.get.await_count == 2

    @pytest.mark.asyncio
    async def test_missing_total_stops_on_empty_page(self, owui_client: OpenWebuiClient) -> None:
        pages = [[{"id": f"m{i}"} for i in range(30)], [{"id": f"m{i}"} for i in range(30, 60)], []]
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.side_effect = _model_pages(pages, total=None)

        result = await owui_client.list_models(mock_client)

        assert len(result) == 60
        assert mock_client.get.await_count == 3

    @pytest.mark.asyncio
    async def test_backstop_raises_when_pagination_never_terminates(
        self, owui_client: OpenWebuiClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(openwebui_client_module, "MODELS_MAX_PAGES", 3)
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(json_data={"items": [{"id": "m"}] * 30, "total": None})

        with pytest.raises(RuntimeError, match="pagination exceeded"):
            await owui_client.list_models(mock_client)

    @pytest.mark.asyncio
    async def test_list_models_handles_bare_list_response(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(json_data=[{"id": "m1"}])

        result = await owui_client.list_models(mock_client)

        assert result == [{"id": "m1"}]
        assert mock_client.get.await_count == 1


MODEL_ID_TAKEN_DETAIL = "Uh-oh! This model id is already registered. Please choose another model id string."


class TestCreateModelIdempotent:
    @pytest.mark.asyncio
    async def test_falls_back_to_update_when_model_id_taken(
        self, owui_client: OpenWebuiClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.side_effect = [
            _response(status_code=401, json_data={"detail": MODEL_ID_TAKEN_DETAIL}),
            _response(json_data={"id": "m1", "name": "Updated"}),
        ]

        with caplog.at_level("WARNING"):
            result = await owui_client.create_model(mock_client, {"id": "m1", "name": "Updated"})

        assert result == {"id": "m1", "name": "Updated"}
        assert mock_client.post.await_count == 2
        assert mock_client.post.await_args_list[1].args[0].endswith("/api/v1/models/model/update")
        assert "already exists" in caplog.text

    @pytest.mark.asyncio
    async def test_raises_on_genuine_unauthorized(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(status_code=401, json_data={"detail": "Unauthorized"})

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.create_model(mock_client, {"id": "m1"})

        assert mock_client.post.await_count == 1


class TestErrorPropagation:
    @pytest.mark.asyncio
    async def test_list_models_raises_on_server_error(self, owui_client: OpenWebuiClient) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get.return_value = _response(status_code=500)

        with pytest.raises(httpx.HTTPStatusError):
            await owui_client.list_models(mock_client)

    @pytest.mark.asyncio
    async def test_create_model_raises_on_validation_error_with_body_attached(
        self, owui_client: OpenWebuiClient
    ) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post.return_value = _response(status_code=422, json_data={"detail": "field required"})

        with pytest.raises(httpx.HTTPStatusError) as excinfo:
            await owui_client.create_model(mock_client, {"id": "test"})

        assert any("field required" in note for note in excinfo.value.__notes__)

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


def _list_response(
    resources: list, *, total_results: int | None = -1, items_per_page: int | None = -1
) -> SimpleNamespace:
    """A SCIM ListResponse stub carrying the fields `_query_all` reads.

    `total_results`/`items_per_page` default to `len(resources)`; pass `None`
    explicitly to simulate a server that omits them.
    """
    return SimpleNamespace(
        resources=resources,
        total_results=len(resources) if total_results == -1 else total_results,
        items_per_page=len(resources) if items_per_page == -1 else items_per_page,
    )


def _paged_query(pages: list[list]):
    """side_effect returning each page in turn, keyed on the requested startIndex."""
    offsets = {}
    cursor = 1
    for page in pages:
        offsets[cursor] = page
        cursor += len(page)
    total = sum(len(p) for p in pages)
    page_size = max((len(p) for p in pages), default=0)

    async def fake_query(model: type, search_request=None, **kwargs):  # noqa: ANN001
        page = offsets.get(search_request.start_index, [])
        return _list_response(page, total_results=total, items_per_page=page_size)

    return fake_query


class TestCreateGroupIdempotent:
    @pytest.mark.asyncio
    async def test_reuses_existing_group_with_same_name(self, owui_client: OpenWebuiClient) -> None:
        existing = _scim_group("aihub:T:R", "grp-existing")
        scim = AsyncMock()
        scim.query.return_value = _list_response([existing])

        result = await owui_client.create_group("aihub:T:R", scim=scim)

        assert result is existing
        scim.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_when_no_group_with_that_name_exists(self, owui_client: OpenWebuiClient) -> None:
        created = _scim_group("aihub:T:R", "grp-new")
        scim = AsyncMock()
        scim.query.return_value = _list_response([_scim_group("aihub:Other:Role", "grp-other")])
        scim.create.return_value = created

        result = await owui_client.create_group("aihub:T:R", scim=scim)

        assert result is created
        scim.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_dedup_scan_walks_all_pages(self, owui_client: OpenWebuiClient) -> None:
        # Target group lives on the SECOND page; create must still find it, not duplicate.
        page1 = [_scim_group(f"aihub:X:{i}", f"g{i}") for i in range(SCIM_PAGE_SIZE)]
        target = _scim_group("aihub:T:R", "grp-target")
        scim = AsyncMock()
        scim.query.side_effect = _paged_query([page1, [target]])

        result = await owui_client.create_group("aihub:T:R", scim=scim)

        assert result is target
        scim.create.assert_not_called()
        assert scim.query.await_count == 2


class TestScimPagination:
    @pytest.mark.asyncio
    async def test_list_users_follows_all_pages(self, owui_client: OpenWebuiClient) -> None:
        page1 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE)]
        page2 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE, SCIM_PAGE_SIZE + 25)]
        scim = AsyncMock()
        scim.query.side_effect = _paged_query([page1, page2])

        result = await owui_client.list_users(scim=scim)

        assert len(result) == SCIM_PAGE_SIZE + 25
        assert scim.query.await_count == 2

    @pytest.mark.asyncio
    async def test_list_users_respects_server_capped_page_size(self, owui_client: OpenWebuiClient) -> None:
        # We ask for SCIM_PAGE_SIZE but the server caps each page at 20 (itemsPerPage=20).
        # Termination must follow the server's page size, not our requested count.
        cap = 20
        total = 45
        users = [User(user_name=f"u{i}@x") for i in range(total)]
        scim = AsyncMock()

        async def fake_query(model: type, search_request=None, **kwargs):  # noqa: ANN001
            start = search_request.start_index - 1
            return _list_response(users[start : start + cap], total_results=total, items_per_page=cap)

        scim.query.side_effect = fake_query

        result = await owui_client.list_users(scim=scim)

        assert len(result) == total
        assert scim.query.await_count == 3  # 20 + 20 + 5

    @pytest.mark.asyncio
    async def test_list_users_handles_missing_total_results(self, owui_client: OpenWebuiClient) -> None:
        # Server omits totalResults; termination relies on a short page.
        page1 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE)]
        page2 = [User(user_name=f"u{i}@x") for i in range(SCIM_PAGE_SIZE, SCIM_PAGE_SIZE + 10)]
        scim = AsyncMock()

        async def fake_query(model: type, search_request=None, **kwargs):  # noqa: ANN001
            page = page1 if search_request.start_index == 1 else page2
            return _list_response(page, total_results=None, items_per_page=SCIM_PAGE_SIZE)

        scim.query.side_effect = fake_query

        result = await owui_client.list_users(scim=scim)

        assert len(result) == SCIM_PAGE_SIZE + 10
        assert scim.query.await_count == 2

    @pytest.mark.asyncio
    async def test_list_groups_stops_on_short_page(self, owui_client: OpenWebuiClient) -> None:
        scim = AsyncMock()
        scim.query.return_value = _list_response([_scim_group("aihub:T:R", "g1")])

        result = await owui_client.list_groups(scim=scim)

        assert len(result) == 1
        assert scim.query.await_count == 1
