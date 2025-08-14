from typing import Annotated

from fastapi import Depends, HTTPException, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.model.dto.ModelDTO import ModelDTO
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller


class ModelController(Controller):
    """
    A controller managing endpoints related to LiteLLM, in order to manage and interact with LiteLLM functionalities.

    ### Why AgentController?
    The AgentController exposes routes for:
    - Listing all available LiteLLM models.
    """

    name = LocaleString(en="Models")
    description = LocaleString(en="Shows all available models.")
    icon = "meteor-icons:key"

    not_authorized_to_view_exception = HTTPException(status_code=403, detail="Not authorized to view this thread")

    def __init__(
        self, *, auth: AuthHandler, route: str = "/models", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def status(self, route: str = "/") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def status(
            user: Annotated[UserIdentity, Depends(self.auth)],
        ) -> dict:
            """
            Get LiteLLM service status.
            """
            return {"status": "ok", "service": "litellm"}

        return self

    def model_list(self, route: str = "/model_list") -> "ModelController":
        @self.router.get(route, tags=self.tags)
        async def model_list(
            nc: Annotated[NATS, Depends(use_nats)],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[ModelDTO]:
            """
            Retrieve a list of all models in LiteLLM.
            """
            # http://localhost:4000/team/daily/activity?start_date=2025-07-11&end_date=2025-08-08&page_size=1000&page=1&exclude_team_ids=litellm-dashboard
            data = [
                ModelDTO(
                    model_name="azure/gpt-4o-mini",
                    mode="chat",
                    max_input_tokens=128000,
                    max_output_tokens=16384,
                    input_cost_per_million_token=1.65e-07 * 1_000_000,
                    cache_read_input_token_cost=7.5e-08 * 1_000_000,
                    output_cost_per_million_token=6.6e-07 * 1_000_000,
                    supports_response_schema=True,
                    supports_vision=True,
                    supports_function_calling=True,
                    supports_tool_choice=True,
                    supports_prompt_caching=True,
                    supported_openai_params=[
                        "temperature",
                        "n",
                        "stream",
                        "stream_options",
                        "stop",
                        "max_tokens",
                        "max_completion_tokens",
                        "tools",
                        "tool_choice",
                        "presence_penalty",
                        "frequency_penalty",
                        "logit_bias",
                        "user",
                        "function_call",
                        "functions",
                        "top_p",
                        "logprobs",
                        "top_logprobs",
                        "response_format",
                        "seed",
                        "extra_headers",
                        "parallel_tool_calls",
                        "prediction",
                        "modalities",
                        "audio",
                        "web_search_options",
                    ],
                ),
                ModelDTO(
                    model_name="text-embedding-3-large",
                    mode="embedding",
                    max_input_tokens=8191,
                    input_cost_per_million_token=1.3e-07 * 1_000_000,
                    input_cost_per_token_batches=6.5e-08 * 1_000_000,
                    output_cost_per_token_batches=0.0 * 1_000_000,
                    output_cost_per_million_token=0.0 * 1_000_000,
                    output_vector_size=3072,
                ),
                ModelDTO(
                    model_name="google/gemini-2.5-flash",
                    mode="chat",
                    max_input_tokens=1048576,
                    max_output_tokens=65535,
                    input_cost_per_million_token=3e-07 * 1_000_000,
                    cache_read_input_token_cost=7.5e-08 * 1_000_000,
                    input_cost_per_audio_token=1e-06 * 1_000_000,
                    output_cost_per_million_token=2.5e-06 * 1_000_000,
                    output_cost_per_reasoning_token=2.5e-06 * 1_000_000,
                    supports_system_messages=True,
                    supports_response_schema=True,
                    supports_vision=True,
                    supports_function_calling=True,
                    supports_tool_choice=True,
                    supports_prompt_caching=True,
                    supports_audio_output=False,
                    supports_pdf_input=True,
                    supports_web_search=True,
                    supports_url_context=True,
                    supports_reasoning=True,
                    tpm=8000000,
                    rpm=100000,
                ),
                ModelDTO(
                    model_name="azure/dall-e-3",
                    mode="image_generation",
                    input_cost_per_million_token=0 * 1_000_000,
                    output_cost_per_million_token=0 * 1_000_000,
                ),
                ModelDTO(
                    model_name="local/qwen3-0.6b",
                    mode="chat",
                    max_input_tokens=32768,
                    max_output_tokens=4096,
                    input_cost_per_million_token=1e-05 * 1_000_000,
                    output_cost_per_million_token=0.0002,
                    supports_function_calling=True,
                ),
            ]
            return data

        return self
