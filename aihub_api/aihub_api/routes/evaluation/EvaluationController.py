from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.access.AccessLevel import AccessLevel
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_agent_event_distributor import (
    use_external_agent_event_distributor,
)
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.routes.Controller import Controller
from fastapi import Body, Depends, HTTPException, Path, Security
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

    This controller provides a structured way to handle operations related to LLM evaluations.
    It allows users to create, retrieve, and update evaluation datasets, as well as manage
    and run evaluation experiments against these datasets. It uses the `EvaluationService`
    to interact with the underlying evaluation framework (Arize Phoenix).
    """

    name = LocaleString(en="Quality Testing", de="Qualitätsprüfung", fr="Tests de qualité", it="Test di qualità")
    description = LocaleString(
        en="Test and evaluate AI assistant quality",
        de="KI-Assistenten testen und bewerten",
        fr="Testez et évaluez la qualité des assistants IA",
        it="Testa e valuta la qualità degli assistenti IA",
    )
    icon = "material-symbols:science-outline"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        judge: LLMConfig,
        route: str = "/evaluations",
        additionally_required_permission: str | None = "aihub.admin.service.evaluation",
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
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
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
        ) -> list[MinimalDataset]:
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
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[MinimalExperiment]:
            experiments = await EvaluationService.get_experiments(t)
            return [
                experiment
                for experiment in experiments
                if AccessChecker.from_user(user).access_level_for_agent(
                    experiment.agent.agent_class, experiment.agent.agent_id
                )
                == AccessLevel.ACCESS_ADMIN
            ]

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
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> Experiment:
            experiment = await EvaluationService.get_experiment(experiment_id, t)
            if (
                AccessChecker.from_user(user).access_level_for_agent(
                    experiment.agent.agent_class, experiment.agent.agent_id
                )
                != AccessLevel.ACCESS_ADMIN
            ):
                raise HTTPException(status_code=403, detail="Only administrators have access to an agents experiments.")
            return experiment

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
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
            nats_client: Annotated[NATS, Depends(use_nats)],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> Experiment:
            if (
                AccessChecker.from_user(user).access_level_for_agent(create_dto.agent_class, create_dto.agent_id)
                != AccessLevel.ACCESS_ADMIN
            ):
                raise HTTPException(
                    status_code=403, detail="Only administrators can create an experiment for this agent."
                )
            return await EvaluationService.run_experiment_evaluation(
                create_dto=create_dto,
                nats_client=nats_client,
                external_agent_event_distributor=external_agent_event_distributor,
                judge=self.judge,
                authenticated_user=user,
                t=t,
            )

        return self
