import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import pandas as pd
import phoenix as px
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.evaluation.PhoenixExperimentEvaluator import PhoenixExperimentEvaluator
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.infrastructure.phoenix.PhoenixSettings import PhoenixSettings
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from nats.aio.client import Client as NATS
from phoenix.client.resources.experiments.types import RanExperiment
from phoenix.experiments.types import Dataset as PhoenixInternalDataset
from phoenix.server.api.routers.v1.datasets import Dataset as PhoenixDataset
from phoenix.server.api.routers.v1.datasets import DatasetWithExampleCount
from phoenix.server.api.routers.v1.experiments import Experiment as PhoenixExperiment

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetItem import DatasetItem
from aihub_api.routes.evaluation.dto.dataset.DatasetItemCreate import DatasetItemCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset
from aihub_api.routes.evaluation.dto.experiment.Experiment import (
    EvaluationData,
    EvaluationSummaryData,
    Experiment,
    ExperimentRunRecord,
)
from aihub_api.routes.evaluation.dto.experiment.ExperimentCreate import ExperimentCreate
from aihub_api.routes.evaluation.dto.experiment.MinimalExperiment import MinimalExperiment

logger = logging.getLogger(__name__)

INPUT_KEY_QUESTION = "question"
OUTPUT_KEY_ANSWER = "answer"


@dataclass
class DataFrameCreationResult:
    dataframe: pd.DataFrame
    input_keys: list[str]
    output_keys: list[str]


class EvaluationService:
    """
    Handles business logic for interacting with Arize Phoenix for LLM evaluations.

    This service abstracts the complexities of interacting with the Phoenix client and its API.
    It separates the data transformation (Pandas DataFrames), HTTP requests, and experiment execution
    logic from the API controller, ensuring a clean and maintainable architecture. It provides
    methods for managing evaluation datasets and running/retrieving experiments.
    """

    @staticmethod
    def _get_phoenix_client() -> px.Client:
        """Initializes and returns a Phoenix client."""
        return px.Client(endpoint=PhoenixSettings().ENDPOINT, warn_if_server_not_running=False)

    @staticmethod
    def _get_phoenix_request_config() -> tuple[str, dict[str, str]]:
        """Resolves the Phoenix base endpoint and authentication headers."""
        auth_token = PhoenixSettings().AUTH_TOKEN
        headers = {"authorization": f"Bearer {auth_token.get_secret_value()}"} if auth_token else {}
        return PhoenixSettings().ENDPOINT, headers

    @staticmethod
    async def _fetch_datasets_from_phoenix() -> list[PhoenixDataset]:
        """Fetches the list of all datasets directly from the Phoenix API."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            return [PhoenixDataset(**dataset) for dataset in response_data.get("data", [])]

    @staticmethod
    async def _fetch_dataset_metadata_from_phoenix(dataset_id: str) -> DatasetWithExampleCount:
        """
        Fetches detailed metadata for a specific dataset_id directly from the Phoenix API.
        # Why direct fetching? The standard phoenix.Client().get_dataset() often returns
        # minimal information, necessitating direct API calls for richer metadata.
        """
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets/{dataset_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            response_json = response.json()
            return DatasetWithExampleCount(**response_json.get("data", response_json))

    @staticmethod
    async def _fetch_experiments_for_dataset_from_phoenix(dataset_id: str) -> list[PhoenixExperiment]:
        """Fetches all experiments associated with a specific dataset ID."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/datasets/{dataset_id}/experiments"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            return [PhoenixExperiment(**exp) for exp in response_data.get("data", [])]

    @staticmethod
    async def _fetch_experiment_meta_from_phoenix(experiment_id: str) -> PhoenixExperiment:
        """Fetches the metadata for a specific experiment ID."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/experiments/{experiment_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return PhoenixExperiment(**response.json().get("data"))

    @staticmethod
    async def _fetch_experiment_json_from_phoenix(experiment_id: str) -> list[dict[str, Any]]:
        """Fetches the detailed run records (JSON output) for a specific experiment ID."""
        base_url, headers = EvaluationService._get_phoenix_request_config()
        url = f"{base_url}/v1/experiments/{experiment_id}/json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _prepare_dataframe_for_upload(items: list[DatasetItemCreate]) -> DataFrameCreationResult:
        """
        Converts DatasetItemCreate DTOs to a Pandas DataFrame.
        # Why Pandas? The Phoenix client library primarily uses Pandas DataFrames
        # for dataset uploads and manipulations.
        """
        input_keys = [INPUT_KEY_QUESTION]
        output_keys = [OUTPUT_KEY_ANSWER]

        if not items:
            return DataFrameCreationResult(
                dataframe=pd.DataFrame(columns=input_keys + output_keys), input_keys=input_keys, output_keys=output_keys
            )

        df_data = [{INPUT_KEY_QUESTION: item.question, OUTPUT_KEY_ANSWER: item.answer} for item in items]
        df = pd.DataFrame(df_data)

        # Ensure standard columns exist even if no data is provided.
        for key in input_keys + output_keys:
            if key not in df.columns:
                df[key] = None
        return DataFrameCreationResult(dataframe=df, input_keys=input_keys, output_keys=output_keys)

    @staticmethod
    @trace_fn
    async def create_dataset(create_dto: DatasetCreate) -> Dataset:
        """Creates a new dataset in Arize Phoenix."""
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

        items_dto = [
            DatasetItem(
                id=str(ex_data.id) if ex_data.id else str(ex_id),
                question=ex_data.input.get(INPUT_KEY_QUESTION, ""),
                answer=ex_data.output.get(OUTPUT_KEY_ANSWER, ""),
            )
            for ex_id, ex_data in (phoenix_dataset_internal.examples or {}).items()
        ]

        return Dataset(
            id=str(phoenix_dataset_internal.id),
            dataset_name=create_dto.dataset_name,
            description=create_dto.description,
            items=items_dto,
            updated_at=datetime.now(UTC),
        )

    @staticmethod
    @trace_fn
    async def update_dataset(dataset_id: str, append_dto: DatasetUpdate) -> Dataset:
        """Appends new items to an existing dataset in Arize Phoenix."""
        client = EvaluationService._get_phoenix_client()
        dataset_meta = await EvaluationService._fetch_dataset_metadata_from_phoenix(dataset_id)
        append_content = EvaluationService._prepare_dataframe_for_upload(append_dto.items)

        phoenix_dataset_internal: PhoenixInternalDataset = client.append_to_dataset(
            dataset_name=dataset_meta.name,
            dataframe=append_content.dataframe,
            input_keys=append_content.input_keys,
            output_keys=append_content.output_keys,
            metadata_keys=[],
        )

        items_dto = [
            DatasetItem(
                id=str(ex_data.id) if ex_data.id else str(ex_id),
                question=ex_data.input.get(INPUT_KEY_QUESTION, ""),
                answer=ex_data.output.get(OUTPUT_KEY_ANSWER, ""),
            )
            for ex_id, ex_data in (phoenix_dataset_internal.examples or {}).items()
        ]

        return Dataset(
            id=str(phoenix_dataset_internal.id),
            dataset_name=dataset_meta.name,
            description=dataset_meta.description,
            items=items_dto,
            created_at=dataset_meta.created_at,
            updated_at=datetime.now(UTC),
        )

    @staticmethod
    @trace_fn
    async def get_dataset(dataset_id: str) -> Dataset:
        """Retrieves detailed information for a specific dataset from Arize Phoenix."""
        client = EvaluationService._get_phoenix_client()
        metadata = await EvaluationService._fetch_dataset_metadata_from_phoenix(dataset_id)
        phoenix_examples_set: PhoenixInternalDataset = client.get_dataset(id=dataset_id)

        items_dto = [
            DatasetItem(
                id=str(ex_data.id) if ex_data.id else str(ex_id),
                question=ex_data.input.get(INPUT_KEY_QUESTION, ""),
                answer=ex_data.output.get(OUTPUT_KEY_ANSWER, ""),
            )
            for ex_id, ex_data in (phoenix_examples_set.examples or {}).items()
        ]

        return Dataset(
            id=dataset_id,
            dataset_name=metadata.name,
            description=metadata.description,
            items=items_dto,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
        )

    @staticmethod
    @trace_fn
    async def get_datasets() -> list[MinimalDataset]:
        """Retrieves a list of summary information for all datasets from Arize Phoenix."""
        datasets = await EvaluationService._fetch_datasets_from_phoenix()
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

    @staticmethod
    @trace_fn
    async def get_experiments(t: LocaleHandler) -> list[MinimalExperiment]:
        """Retrieves a list of summary information for all experiments from Arize Phoenix."""
        experiments_list = []
        datasets = await EvaluationService.get_datasets()

        # Phoenix API organizes experiments under datasets,
        # so we must fetch per-dataset and then aggregate.
        for dataset in datasets:
            phoenix_experiments = await EvaluationService._fetch_experiments_for_dataset_from_phoenix(dataset.id)
            for experiment in phoenix_experiments:
                agent_class = experiment.metadata.get("agent_class")
                agent_id = experiment.metadata.get("agent_id")
                locale = experiment.metadata.get("locale")
                agent_dto = AgentService.get_minimal_agent_instance(agent_class, agent_id, t)
                experiments_list.append(
                    MinimalExperiment(
                        id=experiment.id,
                        name=experiment.metadata.get("experiment_name"),
                        description=experiment.metadata.get("description"),
                        locale=locale,
                        agent=agent_dto,
                        created_at=experiment.created_at,
                        dataset=dataset,
                    )
                )
        return experiments_list

    @staticmethod
    @trace_fn
    async def get_experiment(experiment_id: str, t: LocaleHandler) -> Experiment:
        """Retrieves detailed run results and evaluations for a specific experiment."""
        experiment_meta = await EvaluationService._fetch_experiment_meta_from_phoenix(experiment_id)
        dataset = await EvaluationService.get_dataset(experiment_meta.dataset_id)
        raw_run_records = await EvaluationService._fetch_experiment_json_from_phoenix(experiment_id)

        all_run_records: list[ExperimentRunRecord] = []
        eval_runs_for_summary: list[dict[str, Any]] = []

        # The JSON output provides the richest data, including all
        # annotations and I/O, requiring manual processing to fit our DTOs.
        for record in raw_run_records:
            annotations = record.get("annotations", [])
            conciseness = next((a for a in annotations if a.get("name") == "Conciseness"), None)
            correctness = next((a for a in annotations if a.get("name") == "Correctness"), None)
            completeness = next((a for a in annotations if a.get("name") == "Completeness"), None)

            all_run_records.append(
                ExperimentRunRecord(
                    example_id=record.get("example_id"),
                    question=record.get("input", {}).get(INPUT_KEY_QUESTION),
                    reference_answer=record.get("reference_output", {}).get(OUTPUT_KEY_ANSWER),
                    assistant_answer=record.get("output", {}).get("agent_response"),
                    thread_id=record.get("output", {}).get("thread_id"),
                    display_id=record.get("output", {}).get("display_id"),
                    error=record.get("error"),
                    latency_ms=record.get("latency_ms"),
                    start_time=datetime.fromisoformat(st) if (st := record.get("start_time")) else None,
                    end_time=datetime.fromisoformat(et) if (et := record.get("end_time")) else None,
                    conciseness=EvaluationData(**conciseness) if conciseness else None,
                    correctness=EvaluationData(**correctness) if correctness else None,
                    completeness=EvaluationData(**completeness) if completeness else None,
                )
            )
            eval_runs_for_summary.extend(annotations)

        # Calculate summary statistics for each evaluator.
        # Only create a summary if there are valid scores to average.
        eval_summary: dict[str, EvaluationSummaryData] = {}
        evaluator_names = set(e.get("name") for e in eval_runs_for_summary if e.get("name"))

        for name in evaluator_names:
            specific_evals = [e for e in eval_runs_for_summary if e.get("name") == name]
            scores = [e.get("score") for e in specific_evals if e.get("score") is not None and not e.get("error")]
            if scores:
                eval_summary[name.lower()] = EvaluationSummaryData(
                    evaluator=name,
                    n=len(specific_evals),
                    avg_score=sum(scores) / len(scores),
                )

        agent_class = experiment_meta.metadata.get("agent_class")
        agent_id = experiment_meta.metadata.get("agent_id")
        locale = experiment_meta.metadata.get("locale")
        agent_dto = AgentService.get_minimal_agent_instance(agent_class, agent_id, t)

        return Experiment(
            id=experiment_id,
            name=experiment_meta.metadata.get("experiment_name"),
            description=experiment_meta.metadata.get("experiment_description"),
            created_at=experiment_meta.created_at,
            agent=agent_dto,
            locale=locale,
            dataset=dataset,
            items=all_run_records,
            conciseness=eval_summary.get("conciseness"),
            correctness=eval_summary.get("correctness"),
            completeness=eval_summary.get("completeness"),
        )

    @staticmethod
    @trace_fn
    async def run_experiment_evaluation(
        create_dto: ExperimentCreate,
        nats_client: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        judge: LLMConfig,
        authenticated_user: UserIdentity,
        t: LocaleHandler,
    ) -> Experiment:
        """Runs a new evaluation experiment using the PhoenixExperimentEvaluator."""
        evaluator = PhoenixExperimentEvaluator(
            nats_client=nats_client,
            external_agent_event_distributor=external_agent_event_distributor,
            judge=judge,
            authenticated_user=authenticated_user,
            t=t,
        )

        ran_experiment: RanExperiment = await evaluator.run_evaluation_experiment(
            agent_class=create_dto.agent_class,
            agent_id=create_dto.agent_id,
            dataset_id=create_dto.dataset_id,
            experiment_name=create_dto.experiment_name,
            experiment_description=create_dto.experiment_description,
            experiment_metadata=create_dto.experiment_metadata,
        )

        # After running, fetch the detailed results using our existing method.
        # RanExperiment is a TypedDict, so access via dict syntax
        return await EvaluationService.get_experiment(ran_experiment["experiment_id"], t)
