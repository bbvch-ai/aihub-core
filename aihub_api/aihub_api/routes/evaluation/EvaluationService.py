from dataclasses import dataclass

import httpx
import pandas as pd
import phoenix as px
from typing import List, Tuple, Dict, Any
from datetime import datetime, UTC

from phoenix.experiments.types import Dataset as PhoenixInternalDataset, Experiment as PhoenixExperiment, RanExperiment
from nats.aio.client import Client as NATS

from aihub_api.routes.evaluation.dto.experiment.ExperimentCreate import ExperimentCreate
from aihub_api.routes.evaluation.dto.experiment.Experiment import Experiment
from aihub_api.routes.evaluation.dto.experiment.ExperimentRunResult import ExperimentRunResult, \
    ExperimentRunEvaluationDetail, EvaluationSummaryData, TaskSummaryData
from aihub_api.routes.evaluation.dto.experiment.MinimalExperiment import MinimalExperiment
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.evaluation.Evaluator import PhoenixExperimentEvaluator
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.infrastructure.phoenix.PhoenixConfig import PhoenixConfig
from aihub_api.routes.evaluation.dto.dataset.DatasetItem import DatasetItem
from aihub_api.routes.evaluation.dto.dataset.DatasetItemCreate import DatasetItemCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset
from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor


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

    @staticmethod
    async def get_experiments() -> List[MinimalExperiment]:
        """Retrieves a list of summary information for all experiments from Arize Phoenix."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/experiments" # Verify this endpoint path

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        response_data = response.json()
        experiment_records = response_data.get("data", []) # Assuming similar structure to datasets

        experiments = []
        for record in experiment_records:
            # The fields available from /v1/experiments listing need to be confirmed.
            # This mapping is speculative.
            experiments.append(MinimalExperiment(
                id=record.get("id") or record.get("experiment_id"),
                name=record.get("name", "Unnamed Experiment"),
                description=record.get("description"),
                url=record.get("url"),
                created_at=datetime.fromisoformat(record["created_at"]) if record.get("created_at") else None,
            ))
        return experiments

    @staticmethod
    async def get_experiment_definition(experiment_id: str) -> Experiment:
        """
        Retrieves the definition of a specific experiment by its ID from Arize Phoenix.
        This typically does not include detailed run results.
        """
        client = EvaluationService._get_phoenix_client()
        phoenix_exp_def: PhoenixExperiment = client.get_experiment(experiment_id=experiment_id)

        return Experiment(
            id=str(phoenix_exp_def.id),
            dataset_id=str(phoenix_exp_def.dataset_id),
            dataset_version_id=str(phoenix_exp_def.dataset_version_id),
            repetitions=phoenix_exp_def.repetitions,
            project_name=phoenix_exp_def.project_name,
            name=phoenix_exp_def.project_name,
        )

    @staticmethod
    async def run_experiment_evaluation(
        create_dto: ExperimentCreate,
        nats_client: NATS,
        external_event_distributor: ExternalEventDistributor,
        judge: ChatLLMConfig, # This must be passed in
        authenticated_user: AuthenticatedUser,
    ) -> ExperimentRunResult:
        """
        Runs a new evaluation experiment using the PhoenixExperimentEvaluator and returns detailed results.
        """
        evaluator = PhoenixExperimentEvaluator(
            nats_client=nats_client,
            external_event_distributor=external_event_distributor,
            judge=judge,
            authenticated_user=authenticated_user
        )

        ran_experiment: RanExperiment = await evaluator.run_evaluation_experiment(
            agent_class=create_dto.agent_class,
            agent_id=create_dto.agent_id,
            dataset_id=create_dto.dataset_id,
            agent_system_prompt=create_dto.agent_system_prompt,
            experiment_name=create_dto.experiment_name,
            experiment_description=create_dto.experiment_description,
            experiment_metadata=create_dto.experiment_metadata
        )

        task_summary_data = None
        if ran_experiment.task_summary and not ran_experiment.task_summary.stats.empty:
            # Assuming TaskSummary.stats is a DataFrame with one row
            summary_dict = ran_experiment.task_summary.stats.iloc[0].to_dict()
            task_summary_data = TaskSummaryData(
                n_examples=summary_dict.get('n_examples', 0),
                n_runs=summary_dict.get('n_runs', 0),
                n_errors=summary_dict.get('n_errors', 0),
                top_error=summary_dict.get('top_error')
            )

        eval_summaries_data = []
        if ran_experiment.eval_summaries:
            for summary in ran_experiment.eval_summaries:
                if not summary.stats.empty:
                    # EvaluationSummary.stats has 'evaluator' as index or column
                    # Assuming 'evaluator' is a column after reset_index() if needed
                    df_stats = summary.stats.copy()
                    if 'evaluator' not in df_stats.columns and df_stats.index.name == 'evaluator':
                        df_stats = df_stats.reset_index()

                    for _, row in df_stats.iterrows():
                        eval_summaries_data.append(EvaluationSummaryData(
                            evaluator=row.get('evaluator', 'N/A'),
                            n=row.get('n', 0),
                            n_errors=row.get('n_errors'),
                            top_error=row.get('top_error'),
                            n_scores=row.get('n_scores'),
                            avg_score=row.get('avg_score'),
                            n_labels=row.get('n_labels'),
                            top_2_labels=row.get('top_2_labels')
                        ))

        detailed_evals_df = ran_experiment.get_evaluations() # This is a DataFrame
        detailed_evals_list = [ExperimentRunEvaluationDetail(**row) for row in detailed_evals_df.to_dict(orient='records')]


        return ExperimentRunResult(
            id=str(ran_experiment.id),
            name=ran_experiment.project_name or create_dto.experiment_name or "Unnamed Experiment", # RanExperiment has project_name
            description=create_dto.experiment_description, # Not directly on RanExperiment, take from input
            url=ran_experiment.url,
            dataset_id=str(ran_experiment.dataset_id),
            dataset_version_id=str(ran_experiment.dataset_version_id),
            project_name=ran_experiment.project_name,
            task_summary=task_summary_data,
            evaluation_summaries=eval_summaries_data if eval_summaries_data else None,
            detailed_evaluations=detailed_evals_list if not detailed_evals_df.empty else None
        )