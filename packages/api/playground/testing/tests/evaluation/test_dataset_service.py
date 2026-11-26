"""Tests for DatasetService — Langfuse dataset CRUD operations."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from swiss_ai_hub.api.routes.evaluation.dataset_service import DatasetService
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_create import DatasetCreate
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_item_create import DatasetItemCreate


def _mock_langfuse_dataset(
    *,
    id: str = "ds-1",
    name: str = "test-dataset",
    description: str | None = "A test dataset",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    items: list | None = None,
    tenant_id: str | None = None,
) -> MagicMock:
    ds = MagicMock()
    ds.metadata = {"tenant_id": tenant_id} if tenant_id else None
    ds.id = id
    ds.name = name
    ds.description = description
    ds.created_at = created_at or datetime(2026, 1, 1, tzinfo=UTC)
    ds.updated_at = updated_at or datetime(2026, 1, 2, tzinfo=UTC)
    ds.items = items or []
    return ds


def _mock_langfuse_item(*, id: str = "item-1", question: str = "Q1", answer: str = "A1") -> MagicMock:
    item = MagicMock()
    item.id = id
    item.input = {"question": question}
    item.expected_output = {"answer": answer}
    return item


def _mock_settings(*, public_url: str | None = "http://langfuse:3000", project_id: str | None = "proj-1") -> MagicMock:
    settings = MagicMock()
    settings.PUBLIC_URL = public_url
    settings.PROJECT_ID = project_id
    return settings


TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"


def _list_response(datasets: list, total_pages: int = 1) -> MagicMock:
    response = MagicMock()
    response.data = datasets
    response.meta.total_pages = total_pages
    return response


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def settings() -> MagicMock:
    return _mock_settings()


@pytest.fixture
def service(mock_client: MagicMock, settings: MagicMock) -> DatasetService:
    return DatasetService(mock_client, settings, TENANT)


class TestBuildDatasetUrl:
    """Tests for _build_dataset_url."""

    def test_builds_url(self, service: DatasetService) -> None:
        url = service._build_dataset_url("ds-42")
        assert url == "http://langfuse:3000/project/proj-1/datasets/ds-42"

    def test_strips_trailing_slash(self) -> None:
        svc = DatasetService(MagicMock(), _mock_settings(public_url="http://langfuse:3000/"), TENANT)
        url = svc._build_dataset_url("ds-1")
        assert "//project" not in url

    def test_returns_none_when_public_url_missing(self) -> None:
        svc = DatasetService(MagicMock(), _mock_settings(public_url=None), TENANT)
        assert svc._build_dataset_url("ds-1") is None

    def test_returns_none_when_project_id_missing(self) -> None:
        svc = DatasetService(MagicMock(), _mock_settings(project_id=None), TENANT)
        assert svc._build_dataset_url("ds-1") is None


class TestFetchDatasetById:
    """Tests for _fetch_dataset_by_id."""

    def test_finds_dataset_by_id(self, service: DatasetService, mock_client: MagicMock) -> None:
        ds_meta = _mock_langfuse_dataset(id="ds-1", name="my-dataset", tenant_id=TENANT)
        mock_client.api.datasets.list.return_value = _list_response([ds_meta])
        mock_client.get_dataset.return_value = _mock_langfuse_dataset(name="my-dataset")

        result = service._fetch_dataset_by_id("ds-1")

        mock_client.get_dataset.assert_called_once_with("my-dataset")
        assert result.name == "my-dataset"

    def test_raises_404_for_missing_dataset(self, service: DatasetService, mock_client: MagicMock) -> None:
        mock_client.api.datasets.list.return_value = _list_response([])

        with pytest.raises(HTTPException) as exc_info:
            service._fetch_dataset_by_id("nonexistent")

        assert exc_info.value.status_code == 404


class TestCreateDataset:
    """Tests for create_dataset."""

    @pytest.mark.asyncio
    async def test_creates_dataset_with_items(self, service: DatasetService, mock_client: MagicMock) -> None:
        created_at = datetime(2026, 2, 1, tzinfo=UTC)
        updated_at = datetime(2026, 2, 1, tzinfo=UTC)
        mock_client.api.datasets.list.return_value = _list_response([])
        mock_client.create_dataset.return_value = _mock_langfuse_dataset(
            id="ds-new", created_at=created_at, updated_at=updated_at
        )
        mock_item = MagicMock()
        mock_item.id = "item-new"
        mock_client.create_dataset_item.return_value = mock_item
        mock_client.flush.return_value = None

        dto = DatasetCreate(
            dataset_name="new-ds",
            description="desc",
            items=[DatasetItemCreate(question="Q?", answer="A!")],
        )

        with patch("swiss_ai_hub.api.routes.evaluation.dataset_service.trace_fn", lambda fn: fn):
            result = await service.create_dataset(dto)

        assert result.id == "ds-new"
        assert result.dataset_name == "new-ds"
        assert result.created_at == created_at
        assert result.updated_at == updated_at
        assert len(result.items) == 1
        assert result.items[0].question == "Q?"
        mock_client.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_dataset_with_no_items(self, service: DatasetService, mock_client: MagicMock) -> None:
        mock_client.api.datasets.list.return_value = _list_response([])
        mock_client.create_dataset.return_value = _mock_langfuse_dataset(id="ds-empty")
        mock_client.flush.return_value = None

        dto = DatasetCreate(dataset_name="empty-ds", items=[])

        with patch("swiss_ai_hub.api.routes.evaluation.dataset_service.trace_fn", lambda fn: fn):
            result = await service.create_dataset(dto)

        assert result.id == "ds-empty"
        assert result.items == []


class TestGetDataset:
    """Tests for get_dataset."""

    @pytest.mark.asyncio
    async def test_returns_dataset_with_items(self, service: DatasetService, mock_client: MagicMock) -> None:
        items = [_mock_langfuse_item(id="i1", question="Q1", answer="A1")]
        ds = _mock_langfuse_dataset(id="ds-1", name="test", items=items)

        with patch.object(service, "_fetch_dataset_by_id", return_value=ds):
            result = await service.get_dataset("ds-1")

        assert result.id == "ds-1"
        assert len(result.items) == 1
        assert result.items[0].question == "Q1"


class TestGetDatasets:
    """Tests for get_datasets."""

    @pytest.mark.asyncio
    async def test_returns_minimal_datasets_with_urls(self, service: DatasetService, mock_client: MagicMock) -> None:
        ds1 = _mock_langfuse_dataset(id="ds-1", name="first", tenant_id=TENANT)
        ds2 = _mock_langfuse_dataset(id="ds-2", name="second", tenant_id=TENANT)
        mock_client.api.datasets.list.return_value = _list_response([ds1, ds2])

        result = await service.get_datasets()

        assert len(result) == 2
        assert result[0].langfuse_url == "http://langfuse:3000/project/proj-1/datasets/ds-1"
        assert result[1].langfuse_url == "http://langfuse:3000/project/proj-1/datasets/ds-2"

    @pytest.mark.asyncio
    async def test_returns_empty_list(self, service: DatasetService, mock_client: MagicMock) -> None:
        mock_client.api.datasets.list.return_value = _list_response([])

        result = await service.get_datasets()

        assert result == []


class TestTenantIsolation:
    """All tenants share one Langfuse project; a dataset is only ever reachable from its own tenant."""

    def test_lists_only_the_callers_datasets(self, service: DatasetService, mock_client: MagicMock) -> None:
        own = _mock_langfuse_dataset(id="ds-own", tenant_id=TENANT)
        foreign = _mock_langfuse_dataset(id="ds-foreign", tenant_id=OTHER_TENANT)
        mock_client.api.datasets.list.return_value = _list_response([own, foreign])

        assert [dataset.id for dataset in service._fetch_datasets()] == ["ds-own"]

    def test_another_tenants_dataset_is_not_found(self, service: DatasetService, mock_client: MagicMock) -> None:
        foreign = _mock_langfuse_dataset(id="ds-foreign", tenant_id=OTHER_TENANT)
        mock_client.api.datasets.list.return_value = _list_response([foreign])

        with pytest.raises(HTTPException) as exc_info:
            service._fetch_dataset_by_id("ds-foreign")

        assert exc_info.value.status_code == 404
        mock_client.get_dataset.assert_not_called()

    def test_dataset_without_tenant_belongs_to_the_startup_tenant(self, mock_client: MagicMock) -> None:
        untagged = _mock_langfuse_dataset(id="ds-old")
        mock_client.api.datasets.list.return_value = _list_response([untagged])

        with patch(
            "swiss_ai_hub.api.routes.evaluation.dataset_service.StartupTenantSettings",
            return_value=MagicMock(ID=TENANT),
        ):
            assert [d.id for d in DatasetService(mock_client, _mock_settings(), TENANT)._fetch_datasets()] == ["ds-old"]
            assert DatasetService(mock_client, _mock_settings(), OTHER_TENANT)._fetch_datasets() == []

    def test_reads_every_page(self, service: DatasetService, mock_client: MagicMock) -> None:
        first = _mock_langfuse_dataset(id="ds-1", tenant_id=TENANT)
        second = _mock_langfuse_dataset(id="ds-2", tenant_id=TENANT)
        mock_client.api.datasets.list.side_effect = [_list_response([first], 2), _list_response([second], 2)]

        assert [dataset.id for dataset in service._fetch_datasets()] == ["ds-1", "ds-2"]

    @pytest.mark.asyncio
    async def test_create_records_the_tenant(self, service: DatasetService, mock_client: MagicMock) -> None:
        mock_client.api.datasets.list.return_value = _list_response([])
        mock_client.create_dataset.return_value = _mock_langfuse_dataset(id="ds-new")

        await service.create_dataset(DatasetCreate(dataset_name="new-ds", items=[]))

        assert mock_client.create_dataset.call_args.kwargs["metadata"] == {"tenant_id": TENANT}

    @pytest.mark.asyncio
    async def test_create_rejects_a_name_another_tenant_holds(
        self, service: DatasetService, mock_client: MagicMock
    ) -> None:
        foreign = _mock_langfuse_dataset(id="ds-foreign", name="shared-name", tenant_id=OTHER_TENANT)
        mock_client.api.datasets.list.return_value = _list_response([foreign])

        with pytest.raises(HTTPException) as exc_info:
            await service.create_dataset(DatasetCreate(dataset_name="shared-name", items=[]))

        assert exc_info.value.status_code == 409
        mock_client.create_dataset.assert_not_called()


class TestLangfuseItemToDto:
    """Tests for the static _langfuse_item_to_dto method."""

    def test_converts_valid_item(self) -> None:
        item = _mock_langfuse_item(id="i1", question="Hello?", answer="World!")
        dto = DatasetService._langfuse_item_to_dto(item)

        assert dto.id == "i1"
        assert dto.question == "Hello?"
        assert dto.answer == "World!"

    def test_handles_non_dict_input(self) -> None:
        item = MagicMock()
        item.id = "i2"
        item.input = "not a dict"
        item.expected_output = None

        dto = DatasetService._langfuse_item_to_dto(item)

        assert dto.question == ""
        assert dto.answer == ""
