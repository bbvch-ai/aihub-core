import logging
from collections.abc import AsyncIterator
from typing import Annotated, Literal, Self

from fastapi import Body, Depends, File, Form, Security, UploadFile
from nats.aio.client import Client as NATS
from openai.types import ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose
from openai.types.chat import ChatCompletion
from starlette.responses import StreamingResponse
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.usage import UsageLimits, use_usage_limits
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.distributor import use_external_agent_event_distributor
from swiss_ai_hub.core.distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.routes import Controller

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.dto.embeddings_request import EmbeddingsRequest
from swiss_ai_hub.api.routes.openai.dto.embeddings_response import EmbeddingsResponse
from swiss_ai_hub.api.routes.openai.dto.image_generation_request import ImageGenerationRequest
from swiss_ai_hub.api.routes.openai.dto.model_details import ModelDetails
from swiss_ai_hub.api.routes.openai.dto.model_response import ModelResponse
from swiss_ai_hub.api.routes.openai.dto.text_to_speech_request import TextToSpeechRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

logger = logging.getLogger(__name__)


class OpenaiController(Controller):
    """
    A controller that fully emulates the OpenAI API, enabling AI Hub to serve as a drop-in replacement
    for OpenAI's endpoints.

    The OpenaiController is designed to mirror the exact API interface provided by OpenAI,
    so that customers can seamlessly switch from OpenAI's services to AI Hub without modifying their client code.
    Every endpoint that OpenAI offers - ranging from model management, chat completions, embeddings, image generation,
    to audio processing (both speech-to-text and text-to-speech) - is implemented here with the same
    request/response structure expected by the OpenAI Python and JavaScript SDKs.

    It offers:
    - **API Compatibility**: Provide identical endpoints and interfaces as OpenAI, allowing customers to replace
      OpenAI endpoints with AI Hub's endpoints without changes to their integration.
    - **Unified Access**: Centralize access to various generative AI capabilities (LLM chat, embeddings,
      image generation, STT, and TTS) under a single controller.
    - **Extensibility**: Support multiple underlying model configurations (e.g., Azure, Self-Hosted, ...)
      and validate compatibility where necessary.

    This setup ensures that your backend exposes a fully OpenAI-compatible API interface,
    allowing customers to plug in the OpenAI SDKs directly against AI Hub.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.openai.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.openai.description")
    icon = "mage:message-conversation"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/openai",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_models(self, route: str = "/models") -> Self:
        @self.router.get(
            route,
            summary="List Models",
            description="Lists the currently available models, and provides basic information about each one "
            "such as the owner and availability.",
            response_model=ModelResponse,
            tags=self.tags,
        )
        async def get_models(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> ModelResponse:
            return await OpenaiService.get_models()

        return self

    def get_models_with_assistants(
        self,
        route: str = "/models",
    ) -> Self:
        @self.router.get(
            route,
            summary="List Models (including ai-hub assistants)",
            description="Lists the currently available models and ai-hub assistants, and provides basic information "
            "about each one such as the owner and availability.",
            response_model=ModelResponse,
            tags=self.tags,
        )
        async def get_models_with_assistants(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ModelResponse:
            model_response = await OpenaiService.get_models_with_assistants(t=t)
            access_checker = AccessChecker.from_user(user)
            model_response.data = [
                m
                for m in model_response.data
                if m.object != "assistant" or access_checker.has_access_to_agent(m.agent_class, m.agent_id)
            ]
            return model_response

        return self

    def get_model(self, route: str = "/models/{full_path:path}") -> Self:
        @self.router.get(
            route,
            summary="Retrieve model",
            description="Retrieves a model instance, providing basic information about "
            "the model such as the owner and permissioning.",
            tags=self.tags,
        )
        async def get_model(
            full_path: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> ModelDetails:
            return await OpenaiService.get_model(model_name=full_path)

        return self

    def get_model_with_assistants(self, route: str = "/models/{full_path:path}") -> Self:
        @self.router.get(
            route,
            summary="Retrieve model (including ai-hub assistants)",
            description="Retrieves a model or ai-hub assistant instance, providing basic information "
            "about the model such as the owner and permissioning.",
            tags=self.tags,
        )
        async def get_model_with_assistants(
            full_path: str,
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ModelDetails:
            model = await OpenaiService.get_model_with_assistants(model_name=full_path, t=t)
            access_checker = AccessChecker.from_user(user)
            if not access_checker.has_access_to_agent(model.agent_class, model.agent_id):
                raise ValueError(f"User {user.id} does not have permission to access model {model.name}")

            return model

        return self

    def get_embeddings(self, route: str = "/embeddings") -> Self:
        @self.router.post(
            route,
            summary="Create embeddings",
            description="Creates an embedding vector representing the input text.",
            tags=self.tags,
        )
        async def get_embeddings(
            req: Annotated[EmbeddingsRequest, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> EmbeddingsResponse:
            return await OpenaiService.get_embeddings(
                model_name=req.model,
                input_text=req.input,
                user=user,
                dimensions=req.dimensions,
                encoding_format=req.encoding_format,
            )

        return self

    def chat_completion(self, route: str = "/chat/completions") -> Self:
        @self.router.post(
            route,
            response_model=ChatCompletion,
            summary="Create chat completion",
            description="Creates a model response for the given chat conversation. Learn more in the text generation, "
            "vision, and audio guides. Parameter support can differ depending on the model used to "
            "generate the response, particularly for newer reasoning models. Parameters that are only "
            "supported for reasoning models are noted below. For the current state of unsupported "
            "parameters in reasoning models, refer to the reasoning guide.",
            tags=self.tags,
        )
        async def chat_completion(
            completion_request: Annotated[ChatCompletionRequest, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ChatCompletion | StreamingResponse:
            completion_request.user = completion_request.user or user.id
            return await OpenaiService.chat_completion(
                model_name=completion_request.model,
                chat_completion_request=completion_request,
                user=user,
                t=t,
            )

        return self

    def chat_completion_with_assistants(self, route: str = "/chat/completions") -> Self:
        @self.router.post(
            route,
            response_model=ChatCompletion,
            summary="Create chat completion (including ai-hub assistants)",
            description="Creates a model or ai-hub assistant response for the given chat conversation. "
            "Learn more in the text generation, vision, and audio guides. Parameter support can differ "
            "depending on the model used to generate the response, particularly for newer reasoning "
            "models. Parameters that are only supported for reasoning models are noted below. For the "
            "current state of unsupported parameters in reasoning models, refer to the reasoning guide.",
            tags=self.tags,
        )
        async def chat_completion_with_assistants(
            completion_request: Annotated[ChatCompletionRequest, Body],
            nc: Annotated[NATS, Depends(use_nats)],
            usage_limits: Annotated[UsageLimits, Depends(use_usage_limits)],
            external_agent_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_agent_event_distributor)
            ],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> ChatCompletion | StreamingResponse:
            completion_request.user = completion_request.user or user.id
            model_name = completion_request.model

            if model_name.count("/") == 1:
                agent_class, agent_id = model_name.split("/")
                if not AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id):
                    raise ValueError(f"User {user.id} does not have permission to access model {model_name}")

            return await OpenaiService.chat_completion_with_assistants(
                model_name=model_name,
                chat_completion_request=completion_request,
                user=user,
                nc=nc,
                usage_limits=usage_limits,
                external_agent_event_distributor=external_agent_event_distributor,
                t=t,
            )

        return self

    def generate_image(self, route: str = "/images/generations") -> Self:
        @self.router.post(route, summary="Create image", description="Creates an image given a prompt.", tags=self.tags)
        async def generate_image(
            generation_request: Annotated[ImageGenerationRequest, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> ImagesResponse:
            return await OpenaiService.generate_image(
                model_name=str(generation_request.model),
                image_generation_request=generation_request,
                user=user,
            )

        return self

    def stt(self, route: str = "/audio/transcriptions") -> Self:
        @self.router.post(
            route,
            summary="Create transcription",
            description="Transcribes audio into the input language.",
            tags=self.tags,
        )
        async def create_transcription(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            file: UploadFile = File(..., description="The audio file to transcribe"),
            model: str = Form(..., description="ID of the model to use"),
            language: str | None = Form(None, description="ISO-639-1 language code"),
            prompt: str | None = Form(None, description="Optional text prompt"),
            response_format: str | None = Form("json", description="Format of the response"),
            temperature: float | None = Form(0, description="Sampling temperature between 0 and 1"),
            timestamp_granularities: list[Literal["word", "segment"]] | None = Form(
                None,
                description="Timestamp granularities (e.g. 'word' or 'segment'); "
                "only used with verbose_json response_format",
            ),
        ) -> Transcription | TranscriptionVerbose | str:
            return await OpenaiService.stt(
                model_name=model,
                file=file,
                user=user,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                timestamp_granularities=timestamp_granularities,
            )

        return self

    def tts(self, route: str = "/audio/speech") -> Self:
        @self.router.post(
            route, summary="Create speech", description="Generates audio from the input text.", tags=self.tags
        )
        async def create_speech(
            speech_request: Annotated[TextToSpeechRequest, Body],
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> StreamingResponse:
            tts_response = await OpenaiService.tts(
                model_name=speech_request.model,
                input_text=speech_request.input,
                tts_request=speech_request,
                user=user,
            )

            async def stream_generator() -> AsyncIterator[bytes]:
                # Notice we await the aiter_bytes method to get the async iterator.
                async_iterator = await tts_response.aiter_bytes()
                async for chunk in async_iterator:
                    yield chunk

            media_type = tts_response.response.headers.get("Content-Type", f"audio/{speech_request.response_format}")
            return StreamingResponse(stream_generator(), media_type=media_type)

        return self
