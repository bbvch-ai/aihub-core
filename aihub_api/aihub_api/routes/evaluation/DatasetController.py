from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Body, HTTPException, Path, Security

from aihub_api.routes.evaluation.dto.dataset.Dataset import Dataset
from aihub_api.routes.evaluation.dto.dataset.DatasetCreate import DatasetCreate
from aihub_api.routes.evaluation.dto.dataset.DatasetUpdate import DatasetUpdate
from aihub_api.routes.evaluation.dto.dataset.MinimalDataset import MinimalDataset

from .DatasetService import DatasetService


class DatasetController(Controller):
    """Manages evaluation datasets stored in Langfuse.

    Datasets contain question-answer pairs used to evaluate AI assistant quality.
    Experiments are run directly in the Langfuse UI against these datasets.
    """

    name = LocaleString(en="Datasets", de="Datensätze", fr="Jeux de données", it="Set di dati")
    description = LocaleString(
        en="Manage evaluation datasets for AI assistant testing",
        de="Evaluierungsdatensätze für KI-Assistenten verwalten",
        fr="Gérer les jeux de données d'évaluation des assistants IA",
        it="Gestisci i set di dati di valutazione degli assistenti IA",
    )
    icon = "material-symbols:dataset-outline"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/datasets", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def create_dataset(self, route: str = "/") -> Self:
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
            return await DatasetService.create_dataset(create_dto)

        return self

    def get_datasets(self, route: str = "/") -> Self:
        @self.router.get(
            route,
            tags=self.tags,
            summary="List Evaluation Datasets",
            description="Retrieves a list of all evaluation datasets.",
        )
        async def get_datasets(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
        ) -> list[MinimalDataset]:
            return await DatasetService.get_datasets()

        return self

    def get_dataset(self, route: str = "/{dataset_id}") -> Self:
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
            try:
                return await DatasetService.get_dataset(dataset_id)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        return self

    def update_dataset(self, route: str = "/{dataset_id}") -> Self:
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
            try:
                return await DatasetService.update_dataset(dataset_id, update_dto)
            except ValueError as e:
                raise HTTPException(status_code=404, detail=str(e))

        return self
