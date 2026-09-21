import logging

from fastapi import HTTPException
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure import LiteLLMProxySettings, LiteLLMService, trace_fn

from swiss_ai_hub.api.routes.model.dto.model_dto import ModelDTO, ModelTypeGroupDTO

logger = logging.getLogger(__name__)


class ModelService:
    """
    Provides functionality to retrieve model information.
    """

    @staticmethod
    @trace_fn
    async def get_model_list(user: UserIdentity) -> list[ModelDTO]:
        response = await LiteLLMProxySettings().httpx_aclient.get(
            url="v1/model/info", headers=await LiteLLMService.authorization_header_for_user(user)
        )
        data = response.json()["data"]
        models: list[ModelDTO] = []
        access_checker = AccessChecker.from_user(user)

        for model_data in data:
            model = ModelDTO.model_validate(model_data)

            capability, _, name = model.model_name.partition("/")

            if not name:
                logger.warning(f"Model name '{model.model_name}' does not contain a capability prefix.")
                continue

            if not access_checker.has_access_to_model(capability, name):
                logger.warning(f"User '{user.id}' does not have access to model '{model.model_name}'.")
                continue

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
