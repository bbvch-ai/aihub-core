from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from fastapi import HTTPException
from httpx import Client

from aihub_api.routes.model.dto.ModelDTO import ModelDTO, ModelTypeGroupDTO


class ModelService:
    """
    Provides functionality to retrieve model information.
    """

    @staticmethod
    @trace_fn
    async def get_model_list(user: UserIdentity) -> list[ModelDTO]:
        client: Client = await LiteLLMService.httpx_client_for_user(user)

        response = client.get(url="v1/model/info")
        data = response.json()["data"]
        models: list[ModelDTO] = []

        for model_data in data:
            model = ModelDTO.model_validate(model_data)
            updated_model_info = model.convert_costs_to_microunits()

            updated_model = model.model_copy(update={"model_info": updated_model_info})
            models.append(updated_model)

        return models

    @staticmethod
    @trace_fn
    async def get_model_by_name(user: UserIdentity, model_name: str) -> ModelDTO:
        models = await ModelService.get_model_list(user)

        for model in models:
            if model.model_name == model_name:
                return model

        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

    @staticmethod
    @trace_fn
    async def get_grouped_model_list(user: UserIdentity) -> list[ModelTypeGroupDTO]:
        models = await ModelService.get_model_list(user)

        grouped: dict[str, list[ModelDTO]] = {}

        for model in models:
            model_type = model.model_info.mode or "other"
            if model_type not in grouped:
                grouped[model_type] = []
            grouped[model_type].append(model)

        result = [
            ModelTypeGroupDTO(name=model_type, models=models_in_group)
            for model_type, models_in_group in grouped.items()
        ]

        return sorted(result, key=lambda x: x.name)

    @staticmethod
    @trace_fn
    async def get_models_by_mode(user: UserIdentity, mode: str) -> list[ModelDTO]:
        """Get all models filtered by their mode (chat, embedding, rerank, etc.)."""
        models = await ModelService.get_model_list(user)
        return [model for model in models if model.model_info.mode == mode]
