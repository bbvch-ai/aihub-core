import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.evaluation.LangfuseExperimentEvaluator import LangfuseExperimentEvaluator
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.langfuse.LangfuseSettings import LangfuseSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from langfuse import get_client
from nats.aio.client import Client as NATS

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
class DatasetItemData:
    input: dict[str, Any]
    expected_output: dict[str, Any]
    metadata: dict[str, Any] | None = None


class EvaluationService:
    """
    Handles business logic for interacting with Langfuse for LLM evaluations.

    This service abstracts the complexities of interacting with the Langfuse client and its API.
    It separates the data transformation, HTTP requests, and experiment execution
    logic from the API controller, ensuring a clean and maintainable architecture. It provides
    methods for managing evaluation datasets and running/retrieving experiments.
    """

    @staticmethod
    def _get_langfuse_client() -> Any:
        """Initializes and returns a Langfuse client."""
        # Validate settings are configured - will raise if not
        _ = LangfuseSettings()
        return get_client()

    @staticmethod
    def _prepare_items_for_upload(items: list[DatasetItemCreate]) -> list[DatasetItemData]:
        """Converts DatasetItemCreate DTOs to Langfuse-compatible format."""
        if not items:
            return []

        return [
            DatasetItemData(
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            for item in items
        ]

    @staticmethod
    @trace_fn
    async def create_dataset(create_dto: DatasetCreate) -> Dataset:
        """Creates a new dataset in Langfuse."""
        client = EvaluationService._get_langfuse_client()

        # Create the dataset
        langfuse_dataset = client.create_dataset(
            name=create_dto.dataset_name,
            description=create_dto.description,
        )

        # Add items to the dataset
        items_dto: list[DatasetItem] = []
        for idx, item in enumerate(create_dto.items):
            dataset_item = client.create_dataset_item(
                dataset_name=create_dto.dataset_name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            items_dto.append(
                DatasetItem(
                    id=dataset_item.id,
                    question=item.question,
                    answer=item.answer,
                )
            )

        # Flush to ensure all items are created
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
        """Appends new items to an existing dataset in Langfuse."""
        client = EvaluationService._get_langfuse_client()

        # Get the existing dataset
        dataset = client.get_dataset(dataset_id)

        # Add new items to the dataset
        new_items: list[DatasetItem] = []
        for item in append_dto.items:
            dataset_item = client.create_dataset_item(
                dataset_name=dataset.name,
                input={INPUT_KEY_QUESTION: item.question},
                expected_output={OUTPUT_KEY_ANSWER: item.answer},
            )
            new_items.append(
                DatasetItem(
                    id=dataset_item.id,
                    question=item.question,
                    answer=item.answer,
                )
            )

        # Flush to ensure all items are created
        client.flush()

        # Fetch all items for the complete dataset
        all_items: list[DatasetItem] = []
        for langfuse_item in dataset.items:
            input_data = langfuse_item.input if isinstance(langfuse_item.input, dict) else {}
            output_data = langfuse_item.expected_output if isinstance(langfuse_item.expected_output, dict) else {}
            all_items.append(
                DatasetItem(
                    id=langfuse_item.id,
                    question=input_data.get(INPUT_KEY_QUESTION, ""),
                    answer=output_data.get(OUTPUT_KEY_ANSWER, ""),
                )
            )
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
        """Retrieves detailed information for a specific dataset from Langfuse."""
        client = EvaluationService._get_langfuse_client()
        dataset = client.get_dataset(dataset_id)

        items_dto: list[DatasetItem] = []
        for langfuse_item in dataset.items:
            input_data = langfuse_item.input if isinstance(langfuse_item.input, dict) else {}
            output_data = langfuse_item.expected_output if isinstance(langfuse_item.expected_output, dict) else {}
            items_dto.append(
                DatasetItem(
                    id=langfuse_item.id,
                    question=input_data.get(INPUT_KEY_QUESTION, ""),
                    answer=output_data.get(OUTPUT_KEY_ANSWER, ""),
                )
            )

        return Dataset(
            id=dataset.id,
            dataset_name=dataset.name,
            description=dataset.description,
            items=items_dto,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
        )

    @staticmethod
    @trace_fn
    async def get_datasets() -> list[MinimalDataset]:
        """Retrieves a list of summary information for all datasets from Langfuse."""
        client = EvaluationService._get_langfuse_client()

        # Use Langfuse API to get all datasets
        datasets_response = client.client.datasets.list()
        datasets = datasets_response.data if hasattr(datasets_response, "data") else []

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
        """Retrieves a list of summary information for all experiments from Langfuse."""
        experiments_list: list[MinimalExperiment] = []
        client = EvaluationService._get_langfuse_client()

        # Get all datasets first
        datasets = await EvaluationService.get_datasets()

        # Langfuse organizes experiments (dataset runs) under datasets
        for dataset in datasets:
            try:
                langfuse_dataset = client.get_dataset(dataset.id)
                # Get runs for this dataset
                runs = langfuse_dataset.runs if hasattr(langfuse_dataset, "runs") else []

                for run in runs:
                    metadata = run.metadata if hasattr(run, "metadata") and run.metadata else {}
                    agent_class = metadata.get("agent_class")
                    agent_id = metadata.get("agent_id")
                    locale = metadata.get("locale")
                    agent_dto = AgentService.get_minimal_agent(agent_class, agent_id, t)
                    experiments_list.append(
                        MinimalExperiment(
                            id=run.id if hasattr(run, "id") else run.name,
                            name=metadata.get("experiment_name", run.name if hasattr(run, "name") else ""),
                            description=metadata.get("experiment_description"),
                            locale=locale,
                            agent=agent_dto,
                            created_at=run.created_at if hasattr(run, "created_at") else None,
                            dataset=dataset,
                        )
                    )
            except Exception as e:
                logger.warning(f"Failed to fetch experiments for dataset {dataset.id}: {e}")
                continue

        return experiments_list

    @staticmethod
    @trace_fn
    async def get_experiment(experiment_id: str, t: LocaleHandler) -> Experiment:
        """Retrieves detailed run results and evaluations for a specific experiment."""
        client = EvaluationService._get_langfuse_client()

        # Find the experiment (dataset run) across all datasets
        datasets = await EvaluationService.get_datasets()

        experiment_run = None
        parent_dataset = None

        for dataset_meta in datasets:
            try:
                langfuse_dataset = client.get_dataset(dataset_meta.id)
                runs = langfuse_dataset.runs if hasattr(langfuse_dataset, "runs") else []

                for run in runs:
                    run_id = run.id if hasattr(run, "id") else run.name
                    if run_id == experiment_id or (hasattr(run, "name") and run.name == experiment_id):
                        experiment_run = run
                        parent_dataset = dataset_meta
                        break

                if experiment_run:
                    break
            except Exception:
                continue

        if not experiment_run or not parent_dataset:
            raise ValueError(f"Experiment ID '{experiment_id}' not found in Langfuse.")

        # Fetch the full dataset with items
        dataset = await EvaluationService.get_dataset(parent_dataset.id)

        # Get run items and scores from Langfuse
        all_run_records: list[ExperimentRunRecord] = []
        eval_runs_for_summary: list[dict[str, Any]] = []

        # Access run items
        run_items = experiment_run.dataset_run_items if hasattr(experiment_run, "dataset_run_items") else []

        for run_item in run_items:
            # Extract evaluation scores from the trace
            scores = run_item.scores if hasattr(run_item, "scores") else []
            conciseness_score = None
            correctness_score = None
            completeness_score = None

            for score in scores:
                score_name = score.name if hasattr(score, "name") else ""
                score_value = score.value if hasattr(score, "value") else None
                score_comment = score.comment if hasattr(score, "comment") else None

                eval_data = EvaluationData(
                    name=score_name,
                    score=score_value,
                    label=score_comment,
                )

                if score_name.lower() == "conciseness":
                    conciseness_score = eval_data
                elif score_name.lower() == "correctness":
                    correctness_score = eval_data
                elif score_name.lower() == "completeness":
                    completeness_score = eval_data

                eval_runs_for_summary.append({"name": score_name, "score": score_value, "error": None})

            # Get item input/output
            dataset_item = run_item.dataset_item if hasattr(run_item, "dataset_item") else None
            input_data = dataset_item.input if dataset_item and hasattr(dataset_item, "input") else {}
            expected_output = (
                dataset_item.expected_output if dataset_item and hasattr(dataset_item, "expected_output") else {}
            )
            output_data = run_item.output if hasattr(run_item, "output") else {}

            all_run_records.append(
                ExperimentRunRecord(
                    example_id=run_item.id if hasattr(run_item, "id") else None,
                    question=input_data.get(INPUT_KEY_QUESTION) if isinstance(input_data, dict) else None,
                    reference_answer=(
                        expected_output.get(OUTPUT_KEY_ANSWER) if isinstance(expected_output, dict) else None
                    ),
                    assistant_answer=(
                        output_data
                        if isinstance(output_data, str)
                        else output_data.get("agent_response")
                        if isinstance(output_data, dict)
                        else None
                    ),
                    thread_id=output_data.get("thread_id") if isinstance(output_data, dict) else None,
                    display_id=output_data.get("display_id") if isinstance(output_data, dict) else None,
                    error=run_item.error if hasattr(run_item, "error") else None,
                    latency_ms=run_item.latency if hasattr(run_item, "latency") else None,
                    start_time=run_item.start_time if hasattr(run_item, "start_time") else None,
                    end_time=run_item.end_time if hasattr(run_item, "end_time") else None,
                    conciseness=conciseness_score,
                    correctness=correctness_score,
                    completeness=completeness_score,
                )
            )

        # Calculate summary statistics for each evaluator
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

        metadata = experiment_run.metadata if hasattr(experiment_run, "metadata") and experiment_run.metadata else {}
        agent_class = metadata.get("agent_class")
        agent_id = metadata.get("agent_id")
        locale = metadata.get("locale")
        agent_dto = AgentService.get_minimal_agent(agent_class, agent_id, t)

        return Experiment(
            id=experiment_id,
            name=metadata.get("experiment_name", experiment_id),
            description=metadata.get("experiment_description"),
            created_at=experiment_run.created_at if hasattr(experiment_run, "created_at") else None,
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
        """Runs a new evaluation experiment using the LangfuseExperimentEvaluator."""
        evaluator = LangfuseExperimentEvaluator(
            nats_client=nats_client,
            external_agent_event_distributor=external_agent_event_distributor,
            judge=judge,
            authenticated_user=authenticated_user,
            t=t,
        )

        experiment_result = await evaluator.run_evaluation_experiment(
            agent_class=create_dto.agent_class,
            agent_id=create_dto.agent_id,
            dataset_id=create_dto.dataset_id,
            experiment_name=create_dto.experiment_name,
            experiment_description=create_dto.experiment_description,
            experiment_metadata=create_dto.experiment_metadata,
        )

        # After running, fetch the detailed results using our existing method
        return await EvaluationService.get_experiment(experiment_result["experiment_id"], t)
