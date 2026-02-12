import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any

from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from fastapi import Depends, HTTPException
from langfuse import Langfuse

from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetItem import DatasetItem
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset

INPUT_KEY_QUESTION = "question"
OUTPUT_KEY_ANSWER = "answer"


def get_langfuse_settings() -> LangfuseSettings:
    """FastAPI dependency for Langfuse settings."""
    return LangfuseSettings()


def get_langfuse_client(settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)]) -> Langfuse:
    """FastAPI dependency for Langfuse client."""
    return settings.create_client()


class DatasetService:
    """Handles business logic for Langfuse evaluation datasets.

    Experiments are now managed directly in the Langfuse UI.
    """

    def __init__(self, client: Langfuse, settings: LangfuseSettings) -> None:
        """Initialize service with Langfuse client and settings dependencies."""
        self.client = client
        self._settings = settings

    def _build_dataset_url(self, dataset_id: str) -> str | None:
        """Build the public Langfuse URL for a dataset, or None if not configured."""
        public_url = self._settings.PUBLIC_URL
        project_id = self._settings.PROJECT_ID
        if not public_url or not project_id:
            return None
        return f"{public_url.rstrip('/')}/project/{project_id}/datasets/{dataset_id}"

    def _fetch_datasets(self) -> list[Any]:
        response = self.client.api.datasets.list()
        return getattr(response, "data", [])

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
        langfuse_dataset = await asyncio.to_thread(
            self.client.create_dataset,
            name=create_dto.dataset_name,
            description=create_dto.description,
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
