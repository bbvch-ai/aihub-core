import os

import pandas as pd
import phoenix as px
import httpx # For httpx.HTTPStatusError
from typing import List, Set, Tuple, Optional, Dict
from fastapi import HTTPException
from datetime import datetime
from phoenix.config import get_env_collector_endpoint, get_env_host, get_env_port

from aihub_api.routes.evaluation.dto.EvaluationDatasetDTO import (
    EvaluationDatasetCreateDTO,
    EvaluationDatasetItemDTO,
    EvaluationDatasetResponseDTO,
)
# from aihub_lib.i18n.LocaleHandler import LocaleHandler # If needed for messages

# Ensure Phoenix client environment variables are set:
# PHOENIX_COLLECTOR_ENDPOINT
# PHOENIX_CLIENT_HEADERS (e.g., "api_key=YOUR_PHOENIX_API_KEY") or set api_key in Client constructor

class EvaluationService:
    """
    Service layer for managing evaluation datasets in Arize Phoenix.
    """

    @staticmethod
    def _get_phoenix_client() -> px.Client:
        """Initializes and returns a Phoenix client."""
        try:
            return px.Client(warn_if_server_not_running=False) # warn_if_server_not_running can be set based on environment
        except Exception as e:
            # Log e
            raise HTTPException(status_code=500, detail=f"Failed to initialize Phoenix client: {str(e)}")

    @staticmethod
    def _get_phoenix_client() -> px.Client:
        """Initializes and returns a Phoenix client."""
        try:
            return px.Client(warn_if_server_not_running=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize Phoenix client: {str(e)}")

    @staticmethod
    def _get_phoenix_request_config() -> Tuple[str, Dict[str, str]]:
        """
        Resolves Phoenix base endpoint and authentication headers.
        This mimics how phoenix.Client might resolve its config for direct API calls.
        """
        endpoint_base = get_env_collector_endpoint()
        if not endpoint_base:
            host = get_env_host() or "127.0.0.1" # Default host if None
            if host == "0.0.0.0": # Common practice for servers, client should use localhost
                host = "127.0.0.1"
            port = get_env_port() or 6006 # Default port if None
            endpoint_base = f"http://{host}:{port}"

        headers = {}
        # phoenix.Client __init__ prioritizes api_key param, then headers param, then env vars for headers.
        # For direct calls, we'll primarily check for an API key env var.
        # Note: PHOENIX_CLIENT_HEADERS can be complex; simple Bearer token from API key is easier here.
        api_key = os.getenv("PHOENIX_API_KEY") # Assuming this env var holds the API key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        # else:
        # One might also try to parse os.getenv("PHOENIX_CLIENT_HEADERS")
        # but its format is not standardized for easy parsing here.

        return endpoint_base, headers

    @staticmethod
    def _convert_dto_to_dataframe_and_keys(items: List[EvaluationDatasetItemDTO]) -> Tuple[pd.DataFrame, List[str], List[str], List[str]]:
        """
        Converts a list of DatasetItemDTOs to a Pandas DataFrame and extracts
        input, output, and metadata keys.
        """
        input_k = ["question"]
        output_k = ["answer"]

        if not items:
            return pd.DataFrame(columns=input_k + output_k), input_k, output_k, []

        df_data = []
        all_metadata_keys_set: Set[str] = set()
        for item in items:
            row = {
                "question": item.question,
                "answer": item.answer,
            }
            if item.metadata:
                for key in input_k + output_k:
                    if key in item.metadata:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Metadata key '{key}' is reserved. Please use a different key."
                        )
                row.update(item.metadata)
                all_metadata_keys_set.update(item.metadata.keys())
            df_data.append(row)

        df = pd.DataFrame(df_data)
        metadata_k_list = sorted(list(all_metadata_keys_set))

        for key in metadata_k_list:
            if key not in df.columns:
                df[key] = None # Ensure all metadata columns exist

        # Ensure required columns exist even if items list was empty initially but keys were defined
        for key in input_k + output_k:
            if key not in df.columns:
                df[key] = None

        return df, input_k, output_k, metadata_k_list

    @staticmethod
    async def _convert_phoenix_dataset_to_dto(
            pds: px.experiments.types.Dataset, # This is the object from phoenix client
            input_keys_override: Optional[List[str]] = None,
            output_keys_override: Optional[List[str]] = None,
            metadata_keys_override: Optional[List[str]] = None,
    ) -> EvaluationDatasetResponseDTO:
        """Converts a Phoenix Dataset object to EvaluationDatasetResponseDTO."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets/{pds.id}"

        async with httpx.AsyncClient(timeout=10.0) as client: # Using async httpx client
            response = await client.get(url, headers=headers)
            response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses

        response_data = response.json()
        print("response_data",response_data)

        data = response_data.get("data")

        items_dto = []
        if pds.examples:
            for ex_id, ex_data in pds.examples.items():
                question = ex_data.input.get("question")
                answer = ex_data.output.get("answer")
                if question is None or answer is None:
                    # Log warning about malformed example if necessary
                    continue
                items_dto.append(EvaluationDatasetItemDTO(
                    id=str(ex_data.id) if ex_data.id else str(ex_id), # ex_data.id is preferred
                    question=question,
                    answer=answer,
                    metadata=ex_data.metadata if ex_data.metadata else None
                ))

        # The Dataset object (pds) has pds.id (dataset_id) and pds.version_id
        # Timestamps are not directly on this object for the dataset/version itself.
        # Example.updated_at exists but that's per example.
        # We can set created_at/updated_at to None or approximate if needed later.

        return EvaluationDatasetResponseDTO(
            id=str(pds.id),
            dataset_name=data.get("name"),
            version=str(pds.version_id),
            items=items_dto,
            description=data.get("description"),
            input_keys=input_keys_override,
            output_keys=output_keys_override,
            metadata_keys=metadata_keys_override,
            created_at=data.get("created_at"), # Not directly available on phoenix.experiments.types.Dataset
            updated_at=data.get("updated_at")  # Not directly available on phoenix.experiments.types.Dataset
        )

    @staticmethod
    async def list_datasets(
            # t: LocaleHandler, # If localization needed for potential errors
    ) -> List[EvaluationDatasetResponseDTO]:
        """
        Lists all available datasets from Arize Phoenix.
        This method makes a direct HTTP call as phoenix.Client may not expose this directly.
        """
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client: # Using async httpx client
                response = await client.get(url, headers=headers)
                response.raise_for_status() # Raises HTTPStatusError for 4xx/5xx responses

            response_data = response.json()
            dataset_records = response_data.get("data", [])

            summaries = []
            for record in dataset_records:
                # Adjust field names based on actual API response structure from /v1/datasets
                dataset = await EvaluationService.get_dataset(record.get("id"))
                summaries.append(dataset)
            return summaries
        except httpx.HTTPStatusError as e:
            # Log e.response.text for more details
            raise HTTPException(status_code=e.response.status_code, detail=f"Phoenix API error listing datasets: {e.response.text}")
        except httpx.RequestError as e:
            # For network errors, timeouts, etc.
            # Log e
            raise HTTPException(status_code=503, detail=f"Error connecting to Phoenix to list datasets: {str(e)}")
        except Exception as e:
            # Log e
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred while listing datasets: {str(e)}")


    @staticmethod
    async def create_or_update_dataset(
            dataset_dto: EvaluationDatasetCreateDTO,
            dataset_id: Optional[str] = None
            # t: LocaleHandler, # If localization needed
    ) -> EvaluationDatasetResponseDTO:
        """
        Creates a new dataset in Arize Phoenix or updates it (by creating a new version).
        """
        client = EvaluationService._get_phoenix_client()
        df, input_k, output_k, metadata_k = EvaluationService._convert_dto_to_dataframe_and_keys(dataset_dto.items)

        if df.empty and not dataset_dto.items:
            # Handling for creating a completely empty dataset, if supported/needed.
            # Phoenix's upload_dataset might require at least column definitions or specific handling.
            # For simplicity, assume datasets will have items or this needs specific Phoenix client handling.
            # If allowing empty item list but want to register dataset:
            phoenix_dataset = client.upload_dataset(
                dataset_name=dataset_dto.dataset_name,
                description=dataset_dto.description,
                inputs=[], # No items
                outputs=[],
                metadata=[]
                # input_keys, output_keys, metadata_keys might still be relevant for schema
            )
        elif df.empty and dataset_dto.items: # Should not happen if conversion is correct
            raise HTTPException(status_code=400, detail="Failed to process dataset items into a DataFrame.")
        else:
            try:
                phoenix_dataset = client.upload_dataset(
                    dataframe=df,
                    dataset_name=dataset_dto.dataset_name,
                    input_keys=input_k,
                    output_keys=output_k,
                    metadata_keys=metadata_k,
                    dataset_description=dataset_dto.description,
                )
            except httpx.HTTPStatusError as e:
                # Log e.response.text for more details
                raise HTTPException(status_code=e.response.status_code, detail=f"Phoenix client error on upload: {e.response.text}")
            except Exception as e:
                # Log e
                raise HTTPException(status_code=500, detail=f"Phoenix client error on upload: {str(e)}")

        # For the response, use the data we sent for description and keys
        return await EvaluationService._convert_phoenix_dataset_to_dto(
            phoenix_dataset,
            input_keys_override=input_k,
            output_keys_override=output_k,
            metadata_keys_override=metadata_k
        )

    @staticmethod
    async def get_dataset(
            dataset_id: str,
            # t: LocaleHandler,
    ) -> EvaluationDatasetResponseDTO:
        """
        Retrieves a dataset from Arize Phoenix by its name.
        The returned DTO will have description and key lists as None, as these
        are not part of the minimal phoenix.experiments.types.Dataset object.
        """
        client = EvaluationService._get_phoenix_client()
        try:
            # client.get_dataset can raise ValueError if name not found / not unique,
            # or httpx.HTTPStatusError for other issues.
            phoenix_dataset_obj = client.get_dataset(id=dataset_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found in Phoenix (details fetch).")
            # Log e.response.text
            raise HTTPException(status_code=e.response.status_code, detail=f"Phoenix client error on get: {e.response.text}")
        except Exception as e:
            # Log e
            raise HTTPException(status_code=500, detail=f"Phoenix client error on get: {str(e)}")

        # Description and specific key lists are not on phoenix_dataset_obj.
        return await EvaluationService._convert_phoenix_dataset_to_dto(
            phoenix_dataset_obj,
        )

    # delete_dataset method is removed as phoenix.Client source does not provide it.
    # If a delete mechanism exists (e.g., direct HTTP call if API endpoint is known),
    # it would be added here.