from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService
from httpx import Client

from aihub_api.routes.model.dto.ModelDTO import ModelDTO, ModelInfoDTO


def _convert_costs_to_microunits(model_info: ModelInfoDTO) -> None:
    """Convert cost fields from base units to microunits by multiplying by 1,000,000."""
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

    for field_name in cost_fields:
        current_value = getattr(model_info, field_name)
        if current_value is not None:
            setattr(model_info, field_name, current_value * 1_000_000)


def _set_model_icon(model: ModelDTO):
    if model.model_info.mode == "chat":
        model.icon = "mdi:chat"
    elif model.model_info.mode == "embedding":
        model.icon = "mdi:vector-triangle"
    elif model.model_info.mode == "image_generation":
        model.icon = "mdi:image"
    elif model.model_info.mode in ("audio_transcription", "audio_speech"):
        model.icon = "mdi:microphone"
    else:
        model.icon = "mdi:robot"


class ModelService:
    """
    Provides functionality to retrieve model information.
    """

    @staticmethod
    async def get_model_list(user: UserIdentity) -> list[ModelDTO]:
        client: Client = await LiteLLMService.httpx_client_for_user(user)

        response = client.get(url="v1/model/info")
        data = response.json()["data"]
        models = [ModelDTO.model_validate(model) for model in data]
        for model in models:
            _convert_costs_to_microunits(model.model_info)
            _set_model_icon(model)

        return models
