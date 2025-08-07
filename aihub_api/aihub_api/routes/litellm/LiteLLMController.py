from typing import Annotated

from fastapi import Depends, HTTPException, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.litellm.dto.LLMDTO import LLMDTO, LiteLLMParamsDTO, ModelInfoDTO
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller


class LiteLLMController(Controller):
    """
    A controller managing endpoints related to LiteLLM, in order to manage and interact with LiteLLM functionalities.

    ### Why AgentController?
    The AgentController exposes routes for:
    - Listing all available LiteLLM models.
    """

    name = LocaleString(en="LiteLLM")
    description = LocaleString(en="Interacts with LiteLLM")
    icon = "meteor-icons:key"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")

    def __init__(
        self, *, auth: AuthHandler, route: str = "/litellm", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def status(self, route: str = "/") -> "LiteLLMController":
        @self.router.get(route, tags=self.tags)
        async def status(
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> dict:
            """
            Get LiteLLM service status.
            """
            return {"status": "ok", "service": "litellm"}

        return self

    def model_info(self, route: str = "/model_info") -> "LiteLLMController":
        @self.router.get(route, tags=self.tags)
        async def model_info(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[LLMDTO]:
            """
            Retrieve a list of all models in LiteLLM.
            """
            data = [
                LLMDTO(
                    model_name="azure/gpt-4o-mini",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-12-01-preview",
                        model="azure/gpt-4o-mini",
                    ),
                    model_info=ModelInfoDTO(
                        mode="chat",
                        key="azure/gpt-4o-mini",
                        max_tokens=16384,
                        max_input_tokens=128000,
                        max_output_tokens=16384,
                        input_cost_per_token=1.65e-07,
                        cache_read_input_token_cost=7.5e-08,
                        output_cost_per_token=6.6e-07,
                    ),
                ),
                LLMDTO(
                    model_name="text-embedding-3-large",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-02-01",
                        model="text-embedding-3-large",
                    ),
                    model_info=ModelInfoDTO(
                        mode="embedding",
                        key="text-embedding-3-large",
                        max_tokens=8191,
                        max_input_tokens=8191,
                        input_cost_per_token=1.3e-07,
                        input_cost_per_token_batches=6.5e-08,
                        output_cost_per_token_batches=0.0,
                        output_cost_per_token=0.0,
                        output_vector_size=3072,
                    ),
                ),
                LLMDTO(
                    model_name="google/gemini-2.5-flash",
                    litellm_params=LiteLLMParamsDTO(model="gemini/gemini-2.5-flash"),
                    model_info=ModelInfoDTO(
                        mode="chat",
                        key="gemini/gemini-2.5-flash",
                        max_tokens=65535,
                        max_input_tokens=1048576,
                        max_output_tokens=65535,
                        input_cost_per_token=3e-07,
                        cache_read_input_token_cost=7.5e-08,
                        input_cost_per_audio_token=1e-06,
                        output_cost_per_token=2.5e-06,
                        output_cost_per_reasoning_token=2.5e-06,
                        tpm=8000000,
                        rpm=100000,
                    ),
                ),
            ]
            return data

        return self
