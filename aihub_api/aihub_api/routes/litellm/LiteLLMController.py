from typing import Annotated

from fastapi import Depends, HTTPException, Security
from nats.aio.client import Client as NATS

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.routes.litellm.dto.LLMDTO import LLMDTO, LiteLLMParamsDTO, ModelInfoDTO, CustomTokenizerDTO
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
            # http://localhost:4000/team/daily/activity?start_date=2025-07-11&end_date=2025-08-08&page_size=1000&page=1&exclude_team_ids=litellm-dashboard
            data = [
                LLMDTO(
                    model_name="azure/gpt-4o-mini",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-12-01-preview",
                        use_in_pass_through=False,
                        use_litellm_proxy=False,
                        merge_reasoning_content_in_choices=False,
                        model="azure/gpt-4o-mini",
                    ),
                    model_info=ModelInfoDTO(
                        id="b7461b83483516c44bdd1081929323c456b2b82a5927d5ee482804baf58f535e",
                        db_model=False,
                        mode="chat",
                        key="azure/gpt-4o-mini",
                        max_tokens=16384,
                        max_input_tokens=128000,
                        max_output_tokens=16384,
                        input_cost_per_token=1.65e-07,
                        cache_read_input_token_cost=7.5e-08,
                        output_cost_per_token=6.6e-07,
                        litellm_provider="azure",
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
                ),
                LLMDTO(
                    model_name="text-embedding-3-large",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="https://aihub-dev-openai-che.openai.azure.com/",
                        api_version="2024-02-01",
                        use_in_pass_through=False,
                        use_litellm_proxy=False,
                        merge_reasoning_content_in_choices=False,
                        model="text-embedding-3-large",
                    ),
                    model_info=ModelInfoDTO(
                        id="436d8403029f4dd6fcbaa6b0a17f2332781a37d0a514657936491080dda836a0",
                        db_model=False,
                        mode="embedding",
                        key="text-embedding-3-large",
                        max_tokens=8191,
                        max_input_tokens=8191,
                        input_cost_per_token=1.3e-07,
                        input_cost_per_token_batches=6.5e-08,
                        output_cost_per_token_batches=0.0,
                        output_cost_per_token=0.0,
                        output_vector_size=3072,
                        litellm_provider="openai",
                    ),
                ),
                LLMDTO(
                    model_name="google/gemini-2.5-flash",
                    litellm_params=LiteLLMParamsDTO(
                        use_in_pass_through=False,
                        use_litellm_proxy=False,
                        merge_reasoning_content_in_choices=False,
                        model="gemini/gemini-2.5-flash",
                    ),
                    model_info=ModelInfoDTO(
                        id="796a6f6210a513ed68a5a34f4c66997e49072f665c035dec8a4024e7d60796e3",
                        db_model=False,
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
                        litellm_provider="gemini",
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
                ),
                LLMDTO(
                    model_name="azure/dall-e-3",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="https://joelb-mdotxdzc-australiaeast.cognitiveservices.azure.com/",
                        api_version="2024-02-01",
                        use_in_pass_through=False,
                        use_litellm_proxy=False,
                        merge_reasoning_content_in_choices=False,
                        model="azure/dall-e-3",
                    ),
                    model_info=ModelInfoDTO(
                        id="1c81c0109d0450d2a9bbca4ded2db0ac8c3773b416912699ebebc4777654c79e",
                        db_model=False,
                        base_model="azure/dall-e-3",
                        mode="image_generation",
                        key="azure/dall-e-3",
                        input_cost_per_token=0,
                        output_cost_per_token=0,
                        litellm_provider="azure",
                    ),
                ),
                LLMDTO(
                    model_name="local/qwen3-0.6b",
                    litellm_params=LiteLLMParamsDTO(
                        api_base="http://llama-cpp:8182/v1",
                        use_in_pass_through=False,
                        use_litellm_proxy=False,
                        merge_reasoning_content_in_choices=False,
                        model="openai/unsloth/Qwen3-0.6B-GGUF",
                    ),
                    model_info=ModelInfoDTO(
                        id="7b5627a69223af7fca319f51964386f154eb008c6c6bc659c1ef655090d3258b",
                        db_model=False,
                        mode="chat",
                        key="openai/unsloth/Qwen3-0.6B-GGUF",
                        max_input_tokens=32768,
                        max_output_tokens=4096,
                        input_cost_per_token=1e-05,
                        output_cost_per_token=0.0002,
                        litellm_provider="openai",
                        supports_function_calling=True,
                        custom_tokenizer=CustomTokenizerDTO(
                            identifier="Qwen/Qwen3-0.6B",
                            revision="main",
                        ),
                    ),
                ),
            ]
            return data

        return self
