from typing import Annotated, Self

from fastapi import Body, Depends, Path, Security
from langfuse import Langfuse
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import LangfuseSettings
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset import Dataset
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_create import DatasetCreate
from swiss_ai_hub.api.routes.evaluation.dto.dataset.dataset_update import DatasetUpdate
from swiss_ai_hub.api.routes.evaluation.dto.dataset.minimal_dataset import MinimalDataset

from .dataset_service import DatasetService, get_langfuse_client, get_langfuse_settings


class DatasetController(TenantScopedController):
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
            client: Annotated[Langfuse, Depends(get_langfuse_client)],
            settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)],
        ) -> Dataset:
            service = DatasetService(client, settings)
            return await service.create_dataset(create_dto)

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
            client: Annotated[Langfuse, Depends(get_langfuse_client)],
            settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)],
        ) -> list[MinimalDataset]:
            service = DatasetService(client, settings)
            return await service.get_datasets()

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
            client: Annotated[Langfuse, Depends(get_langfuse_client)],
            settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)],
        ) -> Dataset:
            service = DatasetService(client, settings)
            return await service.get_dataset(dataset_id)

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
            client: Annotated[Langfuse, Depends(get_langfuse_client)],
            settings: Annotated[LangfuseSettings, Depends(get_langfuse_settings)],
        ) -> Dataset:
            service = DatasetService(client, settings)
            return await service.update_dataset(dataset_id, update_dto)

        return self
