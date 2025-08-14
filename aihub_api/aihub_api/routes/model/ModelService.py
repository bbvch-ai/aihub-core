from typing import List

from httpx import Client

from aihub_api.routes.model.dto.ModelDTO import ModelDTO
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.litellm.LiteLLMService import LiteLLMService


class ModelService:
    """
    Provides functionality to retrieve model information.
    """

    @staticmethod
    async def get_model_list(user: UserIdentity) -> List[ModelDTO]:
        client: Client = await LiteLLMService.httpx_client_for_user(user)

        response = client.get(url="v1/model/info")
        data = response.json()["data"]
        models = [ModelDTO.model_validate(model) for model in data]
        for model in models:
            model.model_info.input_cost_per_token *= 1_000_000
            model.model_info.output_cost_per_token *= 1_000_000
        return models
