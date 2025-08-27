from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService
from fastapi import HTTPException
from httpx import Client

from aihub_api.routes.model.dto.ModelDTO import ModelDTO, ModelInfoDTO, ModelTypeGroupDTO


def _convert_costs_to_microunits(model_info: ModelInfoDTO) -> ModelInfoDTO:
    cost_fields = [
        "input_cost_per_token",
        "output_cost_per_token",
        "cache_creation_input_token_cost",
        "cache_read_input_token_cost",
        "input_cost_per_token_above_128k_tokens",
        "input_cost_per_token_above_200k_tokens",
        "input_cost_per_audio_token",
        "input_cost_per_token_batches",
        "output_cost_per_token_batches",
        "output_cost_per_audio_token",
        "output_cost_per_reasoning_token",
        "output_cost_per_token_above_128k_tokens",
        "output_cost_per_token_above_200k_tokens",
        "output_cost_per_image",
        "search_context_cost_per_query",
    ]

    updates = {}
    for field_name in cost_fields:
        current_value = getattr(model_info, field_name)
        if current_value is not None:
            updates[field_name] = current_value * 1_000_000

    return model_info.model_copy(update=updates)


def _get_model_icon(mode: str) -> str:
    if mode == "chat":
        return "mdi:chat"
    elif mode == "embedding":
        return "mdi:vector-triangle"
    elif mode == "image_generation":
        return "mdi:image"
    elif mode in ("audio_transcription", "audio_speech"):
        return "mdi:microphone"
    else:
        return "mdi:robot"


class ModelService:
    """
    Provides functionality to retrieve model information.
    """

    @staticmethod
    async def get_model_list(user: UserIdentity) -> list[ModelDTO]:
        client: Client = await LiteLLMService.httpx_client_for_user(user)

        response = client.get(url="v1/model/info")
        data = response.json()["data"]
        models = []

        for model_data in data:
            model = ModelDTO.model_validate(model_data)
            updated_model_info = _convert_costs_to_microunits(model.model_info)
            icon = _get_model_icon(model.model_info.mode)

            updated_model = model.model_copy(update={"model_info": updated_model_info, "icon": icon})
            models.append(updated_model)

        return models

    @staticmethod
    async def get_model_by_name(user: UserIdentity, model_name: str) -> ModelDTO:
        models = await ModelService.get_model_list(user)

        for model in models:
            if model.model_name == model_name:
                return model

        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")

    @staticmethod
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
