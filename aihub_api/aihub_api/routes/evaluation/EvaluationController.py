from typing import Annotated, List
from fastapi import Path, Body, Security, Depends
from nats.aio.client import Client as NATS

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.routes.Controller import Controller

from .EvaluationService import EvaluationService
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset
from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from .dto.experiment.ExperimentCreate import ExperimentCreate
from .dto.experiment.Experiment import Experiment
from .dto.experiment.ExperimentRunResult import ExperimentRunResult
from .dto.experiment.MinimalExperiment import MinimalExperiment


class EvaluationController(Controller):
    name = LocaleString(en="Evaluation")
    description = LocaleString(en="Manages evaluation datasets stored in Arize Phoenix.")
    icon = "material-symbols:science-outline"

    def __init__(self, judge: ChatLLMConfig, route: str = "/evaluation", auth: AuthHandler | None = None, is_admin_only: bool = True):
        super().__init__(route, auth=auth, is_admin_only=is_admin_only)
        self.judge = judge

    def create_dataset(self, route: str = "/dataset") -> "EvaluationController":
        @self.router.post(route, tags=self.tags)
        async def create_dataset(
            create_dto: Annotated[DatasetCreate, Body()],
            user: AuthenticatedUser = Security(self.auth),
        ) -> Dataset:
            """Creates a new evaluation dataset in Arize Phoenix."""
            return await EvaluationService.create_dataset(create_dto)
        return self

    def get_datasets(self, route: str = "/dataset") -> "EvaluationController":
        @self.router.get(route, tags=self.tags)
        async def get_datasets(
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[MinimalDataset]:
            """Retrieves a list of all evaluation datasets from Arize Phoenix."""
            return await EvaluationService.get_datasets()
        return self

    def get_dataset(self, route: str = "/dataset/{dataset_id}") -> "EvaluationController":
        @self.router.get(route, tags=self.tags)
        async def get_dataset(
            dataset_id: Annotated[str, Path(description="The unique identifier of the dataset to retrieve.")],
            user: AuthenticatedUser = Security(self.auth),
        ) -> Dataset:
            """Retrieves a specific evaluation dataset by its ID, including its items."""
            return await EvaluationService.get_dataset(dataset_id)
        return self

    def update_dataset(self, route: str = "/dataset/{dataset_id}") -> "EvaluationController":
        @self.router.put(route, tags=self.tags)
        async def update_dataset(
            dataset_id: Annotated[str, Path(description="The unique identifier of the dataset to update.")],
            update_dto: Annotated[DatasetUpdate, Body()],
            user: AuthenticatedUser = Security(self.auth),
        ) -> Dataset:
            """
            Appends new question-answer items to an existing evaluation dataset in Arize Phoenix.
            The dataset is identified by its ID.
            """
            return await EvaluationService.update_dataset(dataset_id, update_dto)
        return self

    def get_experiments(self, route: str = "/experiments") -> "EvaluationController":
        @self.router.get(route, tags=["Evaluation Experiments"])
        async def get_experiments(
                user: AuthenticatedUser = Security(self.auth),
        ) -> List[MinimalExperiment]:
            """Retrieves a list of all evaluation experiments from Arize Phoenix."""
            return await EvaluationService.get_experiments()
        return self

    def get_experiment(self, route: str = "/experiments/{experiment_id}") -> "EvaluationController":
        @self.router.get(route, tags=["Evaluation Experiments"])
        async def get_experiment(
                experiment_id: Annotated[str, Path(description="The unique identifier of the experiment to retrieve.")],
                user: AuthenticatedUser = Security(self.auth),
        ) -> Experiment: # Returns the experiment definition
            """Retrieves the definition of a specific evaluation experiment by its ID."""
            return await EvaluationService.get_experiment_definition(experiment_id)
        return self

    def run_experiment(self, route: str = "/experiments") -> "EvaluationController":
        @self.router.post(route, tags=["Evaluation Experiments"], status_code=201)
        async def run_experiment(
                create_dto: Annotated[ExperimentCreate, Body()],
                user: AuthenticatedUser = Security(self.auth),
                nats_client: NATS = Depends(use_nats),
                external_event_distributor: ExternalEventDistributor = Depends(use_external_event_distributor),
        ) -> ExperimentRunResult: # Returns detailed run results
            """
            Creates and runs a new evaluation experiment using the PhoenixExperimentEvaluator.
            The experiment results are logged to Arize Phoenix and detailed results are returned.
            """
            return await EvaluationService.run_experiment_evaluation(
                create_dto=create_dto,
                nats_client=nats_client,
                external_event_distributor=external_event_distributor,
                judge=self.judge,
                authenticated_user=user
            )
        return self
