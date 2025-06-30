from typing import Annotated, List

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, Path, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset
from aihub_api.routes.evaluation.dto.experiment.Experiment import Experiment
from aihub_api.routes.evaluation.dto.experiment.ExperimentCreate import ExperimentCreate
from aihub_api.routes.evaluation.dto.experiment.MinimalExperiment import MinimalExperiment

from .EvaluationService import EvaluationService


class EvaluationController(Controller):
    """
    Manages evaluation datasets and experiments, primarily interfacing with Arize Phoenix.

    ### Why EvaluationController?
    This controller provides a structured way to handle operations related to LLM evaluations.
    It allows users to create, retrieve, and update evaluation datasets, as well as manage
    and run evaluation experiments against these datasets. It uses the `EvaluationService`
    to interact with the underlying evaluation framework (Arize Phoenix).

    ### Authentication
    Endpoints require authentication via the configured `auth` dependency.
    Access is typically restricted to administrators (`is_admin_only=True` by default).
    """

    name = LocaleString(en="Evaluation")
    description = LocaleString(en="Manages evaluation datasets and experiments.")
    icon = "material-symbols:science-outline"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        judge: ChatLLMConfig,
        route: str = "/evaluations",
        is_admin_only: bool = True,
    ):
        super().__init__(auth=auth, route=route, is_admin_only=is_admin_only)
        self.judge = judge

    def create_dataset(self, route: str = "/datasets") -> "EvaluationController":
        @self.router.post(
            route,
            tags=self.tags,
            summary="Create Evaluation Dataset",
            description="Creates a new evaluation dataset.",
        )
        async def create_dataset(
            create_dto: Annotated[DatasetCreate, Body()],
            user: UserIdentity = Security(self.auth),
        ) -> Dataset:
            return await EvaluationService.create_dataset(create_dto)

        return self

    def get_datasets(self, route: str = "/datasets") -> "EvaluationController":
        @self.router.get(
            route,
            tags=self.tags,
            summary="List Evaluation Datasets",
            description="Retrieves a list of all evaluation datasets.",
        )
        async def get_datasets(
            user: UserIdentity = Security(self.auth),
        ) -> List[MinimalDataset]:
            return await EvaluationService.get_datasets()

        return self

    def get_dataset(self, route: str = "/datasets/{dataset_id}") -> "EvaluationController":
        @self.router.get(
            route,
            tags=self.tags,
            summary="Get Specific Dataset",
            description="Retrieves a specific evaluation dataset by its ID, including its items.",
        )
        async def get_dataset(
            dataset_id: Annotated[str, Path(description="The unique identifier of the dataset to retrieve.")],
            user: UserIdentity = Security(self.auth),
        ) -> Dataset:
            return await EvaluationService.get_dataset(dataset_id)

        return self

    def update_dataset(self, route: str = "/datasets/{dataset_id}") -> "EvaluationController":
        @self.router.put(
            route,
            tags=self.tags,
            summary="Update Evaluation Dataset",
            description="Appends new question-answer items to an existing evaluation dataset.",
        )
        async def update_dataset(
            dataset_id: Annotated[str, Path(description="The unique identifier of the dataset to update.")],
            update_dto: Annotated[DatasetUpdate, Body()],
            user: UserIdentity = Security(self.auth),
        ) -> Dataset:
            return await EvaluationService.update_dataset(dataset_id, update_dto)

        return self

    def get_experiments(self, route: str = "/experiments") -> "EvaluationController":
        @self.router.get(
            route,
            tags=self.tags,
            summary="List Evaluation Experiments",
            description="Retrieves a list of all evaluation experiments.",
        )
        async def get_experiments(
            user: UserIdentity = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> List[MinimalExperiment]:
            return await EvaluationService.get_experiments(t)

        return self

    def get_experiment(self, route: str = "/experiments/{experiment_id}") -> "EvaluationController":
        @self.router.get(
            route,
            tags=self.tags,
            summary="Get Specific Experiment",
            description="Retrieves the definition of a specific evaluation experiment by its ID.",
        )
        async def get_experiment(
            experiment_id: Annotated[str, Path(description="The unique identifier of the experiment to retrieve.")],
            user: UserIdentity = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> Experiment:
            return await EvaluationService.get_experiment(experiment_id, t)

        return self

    def run_experiment(self, route: str = "/experiments") -> "EvaluationController":
        @self.router.post(
            route,
            tags=self.tags,
            summary="Run Evaluation Experiment",
            description="Creates and runs a new evaluation experiment.",
        )
        async def run_experiment(
            create_dto: Annotated[ExperimentCreate, Body()],
            user: UserIdentity = Security(self.auth),
            nats_client: NATS = Depends(use_nats),
            external_event_distributor: ExternalEventDistributor = Depends(use_external_event_distributor),
            t: LocaleHandler = Depends(use_locale),
        ) -> Experiment:
            return await EvaluationService.run_experiment_evaluation(
                create_dto=create_dto,
                nats_client=nats_client,
                external_event_distributor=external_event_distributor,
                judge=self.judge,
                authenticated_user=user,
                t=t,
            )

        return self
