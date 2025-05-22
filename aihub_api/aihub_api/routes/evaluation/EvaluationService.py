import os
from dataclasses import dataclass

import httpx
import pandas as pd
import phoenix as px
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, UTC

from phoenix.config import get_env_collector_endpoint, get_env_host, get_env_port
from phoenix.experiments.types import Dataset as PhoenixInternalDataset

from aihub_lib.infrastructure.phoenix.PhoenixConfig import PhoenixConfig
from .dto.DatasetItem import DatasetItem
from .dto.DatasetItemCreate import DatasetItemCreate
from .dto.DatasetCreate import DatasetCreate
from .dto.DatasetUpdate import DatasetUpdate
from .dto.MinimalDataset import MinimalDataset
from .dto.Dataset import Dataset

@dataclass
class DataFrameCreationResult():
    dataframe: pd.DataFrame
    input_keys: List[str]
    output_keys: List[str]

class EvaluationService:

    @staticmethod
    def _get_phoenix_client() -> px.Client:
        """Initializes and returns a Phoenix client configured from environment variables."""
        return px.Client(warn_if_server_not_running=False)

    @staticmethod
    def _get_phoenix_request_config() -> Tuple[str, Dict[str, str]]:
        """
        Resolves the Phoenix base endpoint and authentication headers for direct HTTP calls.
        It attempts to mimic the configuration resolution used by the phoenix.Client.
        """
        endpoint_base = PhoenixConfig().PHOENIX_ENDPOINT
        auth_token = PhoenixConfig().PHOENIX_AUTH_TOKEN
        headers = {"authorization": f"Bearer {auth_token}"} if auth_token else {}

        return endpoint_base, headers

    @staticmethod
    def _prepare_dataframe_for_upload(
            items: List[DatasetItemCreate],
    ) -> DataFrameCreationResult:
        """
        Converts a list of DatasetItemCreate DTOs to a Pandas DataFrame and defines
        standard input/output keys for Phoenix upload.
        """
        input_keys = ["question"]
        output_keys = ["answer"]

        if not items:
            return DataFrameCreationResult(
                dataframe=pd.DataFrame(columns=input_keys + output_keys),
                input_keys=input_keys,
                output_keys=output_keys
            )

        df_data = [{"question": item.question, "answer": item.answer} for item in items]
        df = pd.DataFrame(df_data)

        for key in input_keys + output_keys:
            if key not in df.columns:
                df[key] = None
        return DataFrameCreationResult(
            dataframe=df,
            input_keys=input_keys,
            output_keys=output_keys
        )

    @staticmethod
    async def _fetch_dataset_metadata_from_phoenix(dataset_id: str) -> Dict[str, Any]:
        """
        Fetches detailed metadata for a given dataset_id directly from the Phoenix API.
        This is used because phoenix.Client().get_dataset() returns minimal information.
        """
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets/{dataset_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            response_json = response.json()
            return response_json.get("data", response_json)


    @staticmethod
    async def create_dataset(create_dto: DatasetCreate) -> Dataset:
        """
        Creates a new dataset in Arize Phoenix using the provided name, items, and description.
        Returns the detailed information of the created dataset.
        """
        client = EvaluationService._get_phoenix_client()
        upload_content = EvaluationService._prepare_dataframe_for_upload(create_dto.items)

        phoenix_dataset_internal: PhoenixInternalDataset = client.upload_dataset(
            dataframe=upload_content.dataframe,
            dataset_name=create_dto.dataset_name,
            input_keys=upload_content.input_keys,
            output_keys=upload_content.output_keys,
            metadata_keys=[],
            dataset_description=create_dto.description,
        )

        items_dto = []
        if phoenix_dataset_internal.examples:
            for ex_id, ex_data in phoenix_dataset_internal.examples.items():
                items_dto.append(DatasetItem(
                    id=str(ex_data.id) if ex_data.id else str(ex_id),
                    question=ex_data.input.get("question", ""),
                    answer=ex_data.output.get("answer", ""),
                ))

        return Dataset(
            id=str(phoenix_dataset_internal.id),
            dataset_name=create_dto.dataset_name,
            description=create_dto.description,
            version=str(phoenix_dataset_internal.version_id),
            items=items_dto,
            # created_at/updated_at require a separate fetch if needed immediately and accurately
            updated_at=datetime.now(UTC)
        )

    @staticmethod
    async def update_dataset(dataset_id: str, append_dto: DatasetUpdate) -> Dataset:
        """
        Appends new items to an existing dataset in Arize Phoenix.
        The dataset is identified by dataset_id, its name is resolved for the append operation.
        """
        client = EvaluationService._get_phoenix_client()

        # 1. Fetch existing dataset metadata to get its current name
        dataset_metadata = await EvaluationService._fetch_dataset_metadata_from_phoenix(dataset_id)
        current_dataset_name = dataset_metadata.get("name")
        if not current_dataset_name:
            raise ValueError(f"Could not resolve the name for dataset ID {dataset_id} to append items.")

        # 2. Prepare DataFrame for the new items to append
        append_content = EvaluationService._prepare_dataframe_for_upload(append_dto.items)

        # 3. Call append_to_dataset
        phoenix_dataset_internal: PhoenixInternalDataset = client.append_to_dataset(
            dataset_name=current_dataset_name,
            dataframe=append_content.dataframe,
            input_keys=append_content.input_keys,
            output_keys=append_content.output_keys,
            metadata_keys=[], # No metadata items as per request
        )

        # 4. Construct response DTO from the result of append operation
        # The returned phoenix_dataset_internal represents the new version after appending.
        items_dto = []
        if phoenix_dataset_internal.examples:
            for ex_id, ex_data in phoenix_dataset_internal.examples.items():
                items_dto.append(DatasetItem(
                    id=str(ex_data.id) if ex_data.id else str(ex_id),
                    question=ex_data.input.get("question", ""),
                    answer=ex_data.output.get("answer", ""),
                ))

        # We use the current_dataset_name and potentially updated description from metadata if needed,
        # or assume description doesn't change on append. For now, let's use existing metadata.
        return Dataset(
            id=str(phoenix_dataset_internal.id), # This is the ID of the dataset (should be same as input dataset_id)
            dataset_name=current_dataset_name, # Name should remain the same
            description=dataset_metadata.get("description"), # Preserve original description
            version=str(phoenix_dataset_internal.version_id), # New version ID after append
            items=items_dto, # Items of the new version
            created_at=datetime.fromisoformat(dataset_metadata["created_at"]) if dataset_metadata.get("created_at") else None,
            updated_at=datetime.now(UTC) # Set to current time as it's updated
        )


    @staticmethod
    async def get_dataset(dataset_id: str) -> Dataset:
        """
        Retrieves detailed information for a specific dataset from Arize Phoenix using its ID,
        including its items.
        """
        client = EvaluationService._get_phoenix_client()

        metadata = await EvaluationService._fetch_dataset_metadata_from_phoenix(dataset_id)
        phoenix_examples_set: PhoenixInternalDataset = client.get_dataset(id=dataset_id)

        items_dto = []
        if phoenix_examples_set.examples:
            for ex_id, ex_data in phoenix_examples_set.examples.items():
                items_dto.append(DatasetItem(
                    id=str(ex_data.id) if ex_data.id else str(ex_id),
                    question=ex_data.input.get("question", ""),
                    answer=ex_data.output.get("answer", ""),
                ))

        return Dataset(
            id=dataset_id,
            dataset_name=metadata.get("name", "N/A"),
            description=metadata.get("description"),
            version=str(phoenix_examples_set.version_id) if phoenix_examples_set else metadata.get("latest_version_id"),
            items=items_dto,
            created_at=datetime.fromisoformat(metadata["created_at"]) if metadata.get("created_at") else None,
            updated_at=datetime.fromisoformat(metadata["updated_at"]) if metadata.get("updated_at") else None,
        )

    @staticmethod
    async def get_datasets() -> List[MinimalDataset]:
        """
        Retrieves a list of summary information for all datasets from Arize Phoenix.
        Items are not included in this summary.
        """
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        response_data = response.json()
        dataset_records = response_data.get("data", [])

        summaries = []
        for record in dataset_records:
            summaries.append(MinimalDataset(
                id=record.get("id"),
                dataset_name=record.get("name"),
                description=record.get("description"),
                version=record.get("latest_version_id"),
                created_at=datetime.fromisoformat(record["created_at"]) if record.get("created_at") else None,
                updated_at=datetime.fromisoformat(record["updated_at"]) if record.get("updated_at") else None,
            ))
        return summaries