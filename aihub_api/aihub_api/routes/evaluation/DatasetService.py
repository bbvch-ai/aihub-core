from datetime import UTC, datetime
from typing import Any

from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from langfuse import Langfuse

from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetItem import DatasetItem
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset

INPUT_KEY_QUESTION = "question"
OUTPUT_KEY_ANSWER = "answer"


class DatasetService:
    """Handles business logic for Langfuse evaluation datasets.

    Experiments are now managed directly in the Langfuse UI.
    """

    @staticmethod
    def _get_langfuse_client() -> Langfuse:
        return LangfuseSettings().create_client()

    @staticmethod
    def _fetch_datasets(client: Langfuse) -> list[Any]:
        response = client.api.datasets.list()
        return getattr(response, "data", [])

    @staticmethod
    def _fetch_dataset_by_id(client: Langfuse, dataset_id: str) -> Any:
        """Langfuse requires dataset name for lookup, so we find it by ID first."""
        datasets = DatasetService._fetch_datasets(client)
        dataset_meta = next((d for d in datasets if d.id == dataset_id), None)
        if not dataset_meta:
            raise ValueError(f"Dataset with ID {dataset_id} not found")
        return client.get_dataset(dataset_meta.name)

    @staticmethod
    def _langfuse_item_to_dto(langfuse_item: Any) -> DatasetItem:
        input_data = langfuse_item.input if isinstance(langfuse_item.input, dict) else {}
        output_data = langfuse_item.expected_output if isinstance(langfuse_item.expected_output, dict) else {}
        return DatasetItem(
            id=langfuse_item.id,
            question=input_data.get(INPUT_KEY_QUESTION, ""),
            answer=output_data.get(OUTPUT_KEY_ANSWER, ""),
        )

    @staticmethod
    @trace_fn
    async def create_dataset(create_dto: DatasetCreate) -> Dataset:
        client = DatasetService._get_langfuse_client()

        langfuse_dataset = client.create_dataset(
            name=create_dto.dataset_name,
            description=create_dto.description,
        )

        items_dto: list[DatasetItem] = []
        for item in create_dto.items:
            dataset_item = client.create_dataset_item(
                dataset_name=create_dto.dataset_name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            items_dto.append(DatasetItem(id=dataset_item.id, question=item.question, answer=item.answer))

        client.flush()

        return Dataset(
            id=langfuse_dataset.id,
            dataset_name=create_dto.dataset_name,
            description=create_dto.description,
            items=items_dto,
            updated_at=datetime.now(UTC),
        )

    @staticmethod
    @trace_fn
    async def update_dataset(dataset_id: str, append_dto: DatasetUpdate) -> Dataset:
        client = DatasetService._get_langfuse_client()
        dataset = DatasetService._fetch_dataset_by_id(client, dataset_id)

        new_items: list[DatasetItem] = []
        for item in append_dto.items:
            dataset_item = client.create_dataset_item(
                dataset_name=dataset.name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            new_items.append(DatasetItem(id=dataset_item.id, question=item.question, answer=item.answer))

        client.flush()

        all_items = [DatasetService._langfuse_item_to_dto(item) for item in dataset.items]
        all_items.extend(new_items)

        return Dataset(
            id=dataset.id,
            dataset_name=dataset.name,
            description=dataset.description,
            items=all_items,
            created_at=dataset.created_at,
            updated_at=datetime.now(UTC),
        )

    @staticmethod
    @trace_fn
    async def get_dataset(dataset_id: str) -> Dataset:
        client = DatasetService._get_langfuse_client()
        dataset = DatasetService._fetch_dataset_by_id(client, dataset_id)

        return Dataset(
            id=dataset.id,
            dataset_name=dataset.name,
            description=dataset.description,
            items=[DatasetService._langfuse_item_to_dto(item) for item in dataset.items],
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    @staticmethod
    @trace_fn
    async def get_datasets() -> list[MinimalDataset]:
        client = DatasetService._get_langfuse_client()
        datasets = DatasetService._fetch_datasets(client)

        return [
            MinimalDataset(
                id=dataset.id,
                dataset_name=dataset.name,
                description=dataset.description,
                created_at=dataset.created_at,
                updated_at=dataset.updated_at,
            )
            for dataset in datasets
        ]
