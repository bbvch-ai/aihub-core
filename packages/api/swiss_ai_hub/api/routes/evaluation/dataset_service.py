import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from langfuse import Langfuse
from swiss_ai_hub.core.infrastructure import LangfuseSettings, StartupTenantSettings, trace_fn

from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset import Dataset
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_create import DatasetCreate
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_item import DatasetItem
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_update import DatasetUpdate
from swiss_ai_hub.api.routes.evaluation.dto.dataset.minimal_dataset import MinimalDataset

INPUT_KEY_QUESTION = "question"
OUTPUT_KEY_ANSWER = "answer"
TENANT_METADATA_KEY = "tenant_id"
DATASETS_PAGE_SIZE = 100


def get_langfuse_settings() -> LangfuseSettings:
    """FastAPI dependency for Langfuse settings."""
    return LangfuseSettings()


def get_langfuse_client(settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)]) -> Langfuse:
    """FastAPI dependency for Langfuse client."""
    return settings.create_client()


class DatasetService:
    """Handles business logic for Langfuse evaluation datasets, confined to the caller's tenant.

    All tenants share one Langfuse project, so each dataset records its tenant in its metadata and every read and
    write is filtered by it. Datasets created before that carry no tenant and belong to the startup tenant, the only
    tenant that existed when they were made. Experiments are managed directly in the Langfuse UI.
    """

    def __init__(self, client: Langfuse, settings: LangfuseSettings, tenant_id: str) -> None:
        self.client = client
        self._settings = settings
        self._tenant_id = tenant_id

    def _build_dataset_url(self, dataset_id: str) -> str | None:
        """Build the public Langfuse URL for a dataset, or None if not configured."""
        public_url = self._settings.PUBLIC_URL
        project_id = self._settings.PROJECT_ID
        if not public_url or not project_id:
            return None
        return f"{public_url.rstrip('/')}/project/{project_id}/datasets/{dataset_id}"

    def _fetch_all_datasets(self) -> list[Any]:
        """Every dataset of the shared project; the tenant filter needs all pages, not the first one."""
        datasets: list[Any] = []
        page = 1
        while True:
            response = self.client.api.datasets.list(page=page, limit=DATASETS_PAGE_SIZE)
            datasets.extend(response.data)
            if page >= response.meta.total_pages:
                return datasets
            page += 1

    @staticmethod
    def _tenant_of(dataset: Any) -> str:
        metadata = dataset.metadata if isinstance(dataset.metadata, dict) else {}
        return metadata.get(TENANT_METADATA_KEY) or StartupTenantSettings().ID

    def _fetch_datasets(self) -> list[Any]:
        return [dataset for dataset in self._fetch_all_datasets() if self._tenant_of(dataset) == self._tenant_id]

    def _ensure_name_is_free_for_tenant(self, dataset_name: str) -> None:
        """Langfuse upserts a dataset by name, so a name another tenant holds would hand its dataset over."""
        for dataset in self._fetch_all_datasets():
            if dataset.name == dataset_name and self._tenant_of(dataset) != self._tenant_id:
                raise HTTPException(status_code=409, detail=f"Dataset name {dataset_name} is already taken")

    def _fetch_dataset_by_id(self, dataset_id: str) -> Any:
        """Langfuse requires dataset name for lookup, so we find it by ID first."""
        datasets = self._fetch_datasets()
        dataset_meta = next((d for d in datasets if d.id == dataset_id), None)
        if not dataset_meta:
            raise HTTPException(status_code=404, detail=f"Dataset with ID {dataset_id} not found")
        return self.client.get_dataset(dataset_meta.name)

    @staticmethod
    def _langfuse_item_to_dto(langfuse_item: Any) -> DatasetItem:
        input_data = langfuse_item.input if isinstance(langfuse_item.input, dict) else {}
        output_data = langfuse_item.expected_output if isinstance(langfuse_item.expected_output, dict) else {}
        return DatasetItem(
            id=langfuse_item.id,
            question=input_data.get(INPUT_KEY_QUESTION, ""),
            answer=output_data.get(OUTPUT_KEY_ANSWER, ""),
        )

    @trace_fn
    async def create_dataset(self, create_dto: DatasetCreate) -> Dataset:
        await asyncio.to_thread(self._ensure_name_is_free_for_tenant, create_dto.dataset_name)
        langfuse_dataset = await asyncio.to_thread(
            self.client.create_dataset,
            name=create_dto.dataset_name,
            description=create_dto.description,
            metadata={TENANT_METADATA_KEY: self._tenant_id},
        )

        items_dto: list[DatasetItem] = []
        for item in create_dto.items:
            dataset_item = await asyncio.to_thread(
                self.client.create_dataset_item,
                dataset_name=create_dto.dataset_name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            items_dto.append(DatasetItem(id=dataset_item.id, question=item.question, answer=item.answer))

        await asyncio.wait_for(asyncio.to_thread(self.client.flush), timeout=30.0)

        return Dataset(
            id=langfuse_dataset.id,
            dataset_name=create_dto.dataset_name,
            description=create_dto.description,
            items=items_dto,
            created_at=langfuse_dataset.created_at,
            updated_at=langfuse_dataset.updated_at,
        )

    @trace_fn
    async def update_dataset(self, dataset_id: str, append_dto: DatasetUpdate) -> Dataset:
        dataset = await asyncio.to_thread(self._fetch_dataset_by_id, dataset_id)

        new_items: list[DatasetItem] = []
        for item in append_dto.items:
            dataset_item = await asyncio.to_thread(
                self.client.create_dataset_item,
                dataset_name=dataset.name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            new_items.append(DatasetItem(id=dataset_item.id, question=item.question, answer=item.answer))

        await asyncio.wait_for(asyncio.to_thread(self.client.flush), timeout=30.0)

        all_items = [self._langfuse_item_to_dto(item) for item in dataset.items]
        all_items.extend(new_items)

        return Dataset(
            id=dataset.id,
            dataset_name=dataset.name,
            description=dataset.description,
            items=all_items,
            created_at=dataset.created_at,
            updated_at=datetime.now(UTC),
        )

    @trace_fn
    async def get_dataset(self, dataset_id: str) -> Dataset:
        dataset = await asyncio.to_thread(self._fetch_dataset_by_id, dataset_id)

        return Dataset(
            id=dataset.id,
            dataset_name=dataset.name,
            description=dataset.description,
            items=[self._langfuse_item_to_dto(item) for item in dataset.items],
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    @trace_fn
    async def get_datasets(self) -> list[MinimalDataset]:
        datasets = await asyncio.to_thread(self._fetch_datasets)

        return [
            MinimalDataset(
                id=dataset.id,
                dataset_name=dataset.name,
                description=dataset.description,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
                langfuse_url=self._build_dataset_url(dataset.id),
            )
            for dataset in datasets
        ]
