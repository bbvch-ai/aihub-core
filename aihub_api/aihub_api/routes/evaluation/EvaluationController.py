from typing import Annotated, List
from fastapi import Depends, Path, Body, Security

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller

from .EvaluationService import EvaluationService
from .dto.DatasetCreate import DatasetCreate
from .dto.DatasetUpdate import DatasetUpdate
from .dto.MinimalDataset import MinimalDataset
from .dto.Dataset import Dataset


class EvaluationController(Controller):
    name = LocaleString(en="Evaluation")
    description = LocaleString(en="Manages evaluation datasets stored in Arize Phoenix.")
    icon = "material-symbols:science-outline"

    def __init__(self, route: str = "/evaluation", auth: AuthHandler | None = None, is_admin_only: bool = True):
        super().__init__(route, auth=auth, is_admin_only=is_admin_only)

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