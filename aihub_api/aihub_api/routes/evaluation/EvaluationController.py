from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Security, Path, Body, Query

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.evaluation.EvaluationService import EvaluationService
from aihub_api.routes.evaluation.dto.EvaluationDatasetDTO import (
    EvaluationDatasetCreateDTO,
    EvaluationDatasetResponseDTO,
)

class EvaluationController(Controller):
    """
    Controller for managing evaluation datasets via Arize Phoenix.
    """

    name = LocaleString(en="Evaluation") # More specific name
    description = LocaleString(en="Manages evaluation datasets for AI/LLM models.")
    icon = "material-symbols:science-outline"  # Example icon, changed for datasets

    def __init__(self, route: str = "/evaluations", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def create_evaluation_dataset(self, route: str = "/datasets") -> "EvaluationController":
        @self.router.post(
            route,
            response_model=EvaluationDatasetResponseDTO,
            tags=self.tags,
            summary="Create or Update Evaluation Dataset",
            status_code=201
        )
        async def create_dataset_endpoint(
                dataset_data: Annotated[EvaluationDatasetCreateDTO, Body(...)],
                user: AuthenticatedUser = Security(self.auth),
                t: LocaleHandler = Depends(use_locale),
        ):
            """
            Creates a new evaluation dataset in Arize Phoenix or updates it if it already exists
            (by creating a new version).
            """
            try:
                return await EvaluationService.create_or_update_dataset(dataset_data)
            except HTTPException as e:
                raise e
            except Exception as e:
                # Log the exception e
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        return self

    def list_evaluation_datasets(self, route: str = "/datasets") -> "EvaluationController":
        @self.router.get(
            route, # This will be GET /evaluations/datasets
            response_model=List[EvaluationDatasetResponseDTO],
            tags=self.tags,
            summary="List All Evaluation Datasets"
        )
        async def list_datasets_endpoint(
                user: AuthenticatedUser = Security(self.auth),
                t: LocaleHandler = Depends(use_locale),
        ):
            """
            Retrieves a list of summary information for all available evaluation datasets
            from Arize Phoenix.
            """
            try:
                return await EvaluationService.list_datasets() # Use await if service method is async
            except HTTPException as e:
                raise e
            except Exception as e:
                # Log e
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        return self

    def get_evaluation_dataset(self, route: str = "/datasets/{dataset_id}") -> "EvaluationController":
        @self.router.get(
            route,
            response_model=EvaluationDatasetResponseDTO,
            tags=self.tags,
            summary="Get Evaluation Dataset by Name"
        )
        async def get_dataset_endpoint(
                dataset_id: Annotated[str, Path(..., description="The ID of the dataset to retrieve from Phoenix.")],
                user: AuthenticatedUser = Security(self.auth),
                t: LocaleHandler = Depends(use_locale),
        ):
            """
            Retrieves a specific evaluation dataset from Arize Phoenix by its name.
            Note: Some fields like full description or precise original key configurations
            might be limited if not directly available on the fetched Phoenix Dataset object.
            """
            try:
                return await EvaluationService.get_dataset(dataset_id)
            except HTTPException as e:
                raise e
            except Exception as e:
                # Log e
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        return self

    def update_evaluation_dataset(self, route: str = "/datasets/{dataset_id}") -> "EvaluationController":
        @self.router.put(
            route,
            response_model=EvaluationDatasetResponseDTO,
            tags=self.tags,
            summary="Update Evaluation Dataset by Name"
        )
        async def update_dataset_endpoint(
                dataset_id: Annotated[str, Path(..., description="The ID of the dataset to retrieve from Phoenix.")],
                dataset_data: Annotated[EvaluationDatasetCreateDTO, Body(...)],
                user: AuthenticatedUser = Security(self.auth),
                t: LocaleHandler = Depends(use_locale),
        ):
            """
            Updates an existing evaluation dataset in Arize Phoenix by creating a new version.
            The `dataset_name` in the path must match `dataset_data.dataset_name`.
            """
            try:
                return await EvaluationService.create_or_update_dataset(dataset_id, dataset_data)
            except HTTPException as e:
                raise e
            except Exception as e:
                # Log e
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
        return self

    # delete_evaluation_dataset method is removed as the phoenix.Client source
    # does not provide a public method for dataset deletion.
    # If this functionality is critical, the Phoenix API would need to be
    # checked for a direct HTTP DELETE endpoint, or the client extended.