from dataclasses import dataclass

import httpx
import pandas as pd
import phoenix as px
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, UTC

from phoenix.experiments.types import Dataset as PhoenixInternalDataset, RanExperiment
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.evaluation.dto.experiment.Experiment import Experiment, EvaluationData
from aihub_api.routes.evaluation.dto.experiment.Experiment import ExperimentRunRecord, \
    EvaluationSummaryData
from aihub_api.routes.evaluation.dto.experiment.ExperimentCreate import ExperimentCreate
from aihub_api.routes.evaluation.dto.experiment.MinimalExperiment import MinimalExperiment
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.evaluation.Evaluator import PhoenixExperimentEvaluator
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
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
    async def get_experiments(t: LocaleHandler) -> List[MinimalExperiment]:
        """Retrieves a list of summary information for all experiments from Arize Phoenix."""
        base_url, headers = EvaluationService._get_phoenix_request_config()

        experiments = []
        datasets = await EvaluationService.get_datasets()
        async with httpx.AsyncClient(timeout=10.0) as client:
            for dataset in datasets:
                url = f"{base_url}/v1/datasets/{dataset.id}/experiments"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                print("response data", response_data)
                experiment_records = response_data.get("data", [])


                for record in experiment_records:
                    agent_class = record.get("metadata", {}).get("agent_class")
                    agent_id = record.get("metadata", {}).get("agent_id")
                    agent_dto = AgentService.get_minimal_agent(agent_class, agent_id, t)
                    experiments.append(MinimalExperiment(
                        id=record.get("id"),
                        name=record.get("metadata", {}).get("experiment_name"),
                        description=record.get("metadata", {}).get("description"),
                        agent=agent_dto,
                        created_at=datetime.fromisoformat(record["created_at"]) if record.get("created_at") else None,
                        dataset=dataset,
                    ))
        return experiments

    @staticmethod
    async def get_experiment(experiment_id: str, t: LocaleHandler) -> Experiment: # Changed return type
        """
        Retrieves detailed run results and evaluations for a specific experiment by its ID.
        It fetches data from the /v1/experiments/{id}/json endpoint.
        """
        base_url, headers = EvaluationService._get_phoenix_request_config()

        async with httpx.AsyncClient(timeout=30.0) as http_client: # Longer timeout for potentially large JSON
            response = await http_client.get(f"{base_url}/v1/experiments/{experiment_id}", headers=headers)
            response.raise_for_status()
            experiment_data = response.json().get("data")

            dataset = await EvaluationService.get_dataset(experiment_data.get("dataset_id"))

        all_run_records: List[ExperimentRunRecord] = []
        task_runs_for_summary: List[Dict[str, Any]] = []
        eval_runs_for_summary: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(f"{base_url}/v1/experiments/{experiment_id}/json", headers=headers)
            response.raise_for_status()
            raw_run_records = response.json()

            for record in raw_run_records:
                annotations = record.get("annotations", [])
                conciseness = [a for a in annotations if a.get("name") == "Conciseness"]
                correctness = [a for a in annotations if a.get("name") == "Correctness"]
                completeness = [a for a in annotations if a.get("name") == "Completeness"]
                all_run_records.append(ExperimentRunRecord(
                    example_id=record.get("example_id"),
                    question=record.get("input").get("question"),
                    reference_answer=record.get("reference_output").get("answer"),
                    assistant_answer=record.get("output").get("agent_response"),
                    error=record.get("error"),
                    latency_ms=record.get("latency_ms"),
                    start_time=datetime.fromisoformat(record["start_time"]) if record.get("start_time") else datetime.now(UTC),
                    end_time=datetime.fromisoformat(record["end_time"]) if record.get("end_time") else datetime.now(UTC),
                    conciseness=EvaluationData(**conciseness[0]) if conciseness else None,
                    correctness=EvaluationData(**correctness[0]) if correctness else None,
                    completeness=EvaluationData(**completeness[0]) if completeness else None,
                ))
                task_runs_for_summary.append({"error": record.get("error")})
                for annotation in record.get("annotations", []):
                    eval_runs_for_summary.append({
                        "evaluator": annotation.get("name"),
                        "error": annotation.get("error"),
                        "score": annotation.get("score"),
                        "label": annotation.get("label")
                    })

        eval_summary: Dict[str, EvaluationSummaryData] = {}
        evaluator_names = set(e.get("evaluator") for e in eval_runs_for_summary if e.get("evaluator"))

        for name in evaluator_names:
            specific_evals = [e for e in eval_runs_for_summary if e.get("evaluator") == name]
            scores = [e.get("score") for e in specific_evals if e.get("score") is not None and not e.get("error")]

            eval_summary[name.lower()] = EvaluationSummaryData(
                evaluator=name,
                n=len(specific_evals),
                avg_score=sum(scores) / len(scores) if scores else None,
            )

        agent_class = experiment_data.get("metadata", {}).get("agent_class")
        agent_id = experiment_data.get("metadata", {}).get("agent_id")
        agent_dto = AgentService.get_minimal_agent(agent_class, agent_id, t)

        return Experiment(
            id=experiment_id,
            name=experiment_data.get("metadata", {}).get("experiment_name"),
            description=experiment_data.get("metadata", {}).get("experiment_description"),
            created_at=experiment_data.get("created_at"),
            agent=agent_dto,
            dataset=dataset,
            items=all_run_records,
            conciseness=eval_summary.get("correctness"),
            correctness=eval_summary.get("correctness"),
            completeness=eval_summary.get("completeness"),
        )



    @staticmethod
    async def run_experiment_evaluation(
        create_dto: ExperimentCreate,
        nats_client: NATS,
        external_event_distributor: ExternalEventDistributor,
        judge: ChatLLMConfig, # This must be passed in
        authenticated_user: AuthenticatedUser,
        t: LocaleHandler,
    ) -> Experiment:
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
            experiment_name=create_dto.experiment_name,
            experiment_description=create_dto.experiment_description,
            experiment_metadata=create_dto.experiment_metadata
        )

        return await EvaluationService.get_experiment(ran_experiment.id, t)