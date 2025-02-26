import logging
from typing import Annotated, Any, AsyncIterator, Callable, List, Literal, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from aihub_lib.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from fastapi import Body, Depends, File, Form, Security, UploadFile
from llama_index.llms.openai import OpenAI
from nats.aio.client import Client as NATS
from openai.types import ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose
from openai.types.chat import ChatCompletion
from starlette.responses import StreamingResponse

from .dto.ChatCompletionRequest import ChatCompletionRequest
from .dto.EmbeddingsRequest import EmbeddingsRequest
from .dto.EmbeddingsResponse import EmbeddingsResponse
from .dto.ImageGenerationRequest import ImageGenerationRequest
from .dto.ModelDetails import ModelDetails
from .dto.ModelResponse import ModelResponse
from .dto.TextToSpeechRequest import TextToSpeechRequest
from .OpenaiService import OpenaiService
from ...i18n.dependencies.use_locale import use_locale

logger = logging.getLogger(__name__)


class OpenaiController(Controller):
    """
    A controller that fully emulates the OpenAI API, enabling AI Hub to serve as a drop-in replacement for OpenAI's endpoints.

    ### Why OpenaiController?
    The OpenaiController is designed to mirror the exact API interface provided by OpenAI, so that customers can seamlessly switch
    from OpenAI's services to AI Hub without modifying their client code. Every endpoint that OpenAI offers—ranging from model management,
    chat completions, embeddings, image generation, to audio processing (both speech-to-text and text-to-speech)—is implemented here with the same
    request/response structure expected by the OpenAI Python and JavaScript SDKs.

    ### Key Intentions
    - **API Compatibility**: Provide identical endpoints and interfaces as OpenAI, allowing customers to replace OpenAI endpoints with AI Hub's
      endpoints without changes to their integration.
    - **Unified Access**: Centralize access to various generative AI capabilities (LLM chat, embeddings, image generation, STT, and TTS)
      under a single controller.
    - **Extensibility**: Support multiple underlying model configurations (e.g., Azure, Self-Hosted, ...) and validate compatibility where necessary.

    This setup ensures that your backend exposes a fully OpenAI-compatible API interface, allowing customers to plug in the
    OpenAI SDKs directly against AI Hub.
    """
    name = LocaleString(en="OpenAI")
    description = LocaleString(en="OpenAI Compatible API")
    icon = "simple-icons:openai"

    def __init__(
        self,
        route: str = "/openai",
        auth: AuthHandler | None = None,
        is_admin_only=False,
        embedding_models: List[EmbeddingLLMConfig] = None,
        chat_models: List[ChatLLMConfig] = None,
        image_models: List[AzureOpenaiImageModelConfig] = None,
        stt_models: List[AzureOpenaiSTTConfig] = None,
        tts_models: List[AzureOpenaiTTSConfig] = None,
    ):
        super().__init__(route, auth, is_admin_only=is_admin_only)
        self.embedding_models = embedding_models or []
        self.chat_models = chat_models or []
        self.image_models = image_models or []
        self.tts_models = tts_models or []
        self.stt_models = stt_models or []

        # Validate that all chat models are OpenAI compatible
        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def get_models(self, route: str = "/models") -> "OpenaiController":
        @self.router.get(
            route,
            summary="List Models",
            description="Lists the currently available models, and provides basic information about each one such as the owner and availability.",
            response_model=ModelResponse,
            tags=self.tags
        )
        async def get_models(
            user: AuthenticatedUser = Security(self.auth),
        ) -> ModelResponse:
            return OpenaiService.get_models(self.chat_models)

        return self

    def get_models_with_assistants(self, route: str = "/models") -> "OpenaiController":
        @self.router.get(
            route,
            summary="List Models (including ai-hub assistants)",
            description="Lists the currently available models and ai-hub assistants, and provides basic information about each one such as the owner and availability.",
            response_model=ModelResponse,
            tags=self.tags
        )
        async def get_models(
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ModelResponse:
            return await OpenaiService.get_models_with_assistants(self.chat_models, user, nc, t)

        return self

    def get_model(self, route: str = "/models/{full_path:path}") -> "OpenaiController":
        @self.router.get(
            route,
            summary="Retrieve model",
            description="Retrieves a model instance, providing basic information about the model such as the owner and permissioning.",
            tags=self.tags
        )
        async def get_model(
            full_path: str,
            user: AuthenticatedUser = Security(self.auth),
        ) -> ModelDetails:
            return OpenaiService.get_model(self.chat_models, model_name=full_path)

        return self

    def get_model_with_assistants(self, route: str = "/models/{full_path:path}") -> "OpenaiController":
        @self.router.get(
            route,
            summary="Retrieve model (including ai-hub assistants)",
            description="Retrieves a model or ai-hub assistant instance, providing basic information about the model such as the owner and permissioning.",
            tags=self.tags
        )
        async def get_model(
            full_path: str,
            nc: Annotated[NATS, Depends(use_nats)],
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ModelDetails:
            return await OpenaiService.get_model_with_assistants(
                self.chat_models, model_name=full_path, user=user, nc=nc, t=t
            )

        return self

    def get_embeddings(self, route: str = "/embeddings") -> "OpenaiController":
        @self.router.post(
            route,
            summary="Create embeddings",
            description="Creates an embedding vector representing the input text.",
            tags=self.tags
        )
        async def get_embeddings(
            req: Annotated[EmbeddingsRequest, Body],
            user: AuthenticatedUser = Security(self.auth),
        ) -> EmbeddingsResponse:
            return OpenaiService.get_embeddings(
                self.embedding_models,
                req.model,
                req.input,
                dimensions=req.dimensions,
                encoding_format=req.encoding_format,
            )

        return self

    def chat_completion(self, route: str = "/chat/completions") -> "OpenaiController":
        @self.router.post(
            route,
            response_model=ChatCompletion,
            summary="Create chat completion",
            description="Creates a model response for the given chat conversation. Learn more in the text generation, vision, and audio guides. Parameter support can differ depending on the model used to generate the response, particularly for newer reasoning models. Parameters that are only supported for reasoning models are noted below. For the current state of unsupported parameters in reasoning models, refer to the reasoning guide.",
            tags=self.tags
        )
        async def chat_completion(
            completion_request: Annotated[ChatCompletionRequest, Body],
            user: AuthenticatedUser = Security(self.auth),
        ) -> ChatCompletion | StreamingResponse:
            return await OpenaiService.chat_completion(
                self.chat_models, completion_request.model, completion_request.model_dump()
            )

        return self

    def chat_completion_with_assistants(self, route: str = "/chat/completions") -> "OpenaiController":
        @self.router.post(
            route,
            response_model=ChatCompletion,
            summary="Create chat completion (including ai-hub assistants)",
            description="Creates a model or ai-hub assistant response for the given chat conversation. Learn more in the text generation, vision, and audio guides. Parameter support can differ depending on the model used to generate the response, particularly for newer reasoning models. Parameters that are only supported for reasoning models are noted below. For the current state of unsupported parameters in reasoning models, refer to the reasoning guide.",
            tags=self.tags
        )
        async def chat_completion(
            completion_request: Annotated[ChatCompletionRequest, Body],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
            user: AuthenticatedUser = Security(self.auth),
            t: LocaleHandler = Depends(use_locale),
        ) -> ChatCompletion | StreamingResponse:
            return await OpenaiService.chat_completion_with_assistants(
                self.chat_models, completion_request.model, completion_request, user, nc, ws_receiver, t
            )

        return self

    def generate_image(self, route: str = "/images/generations") -> "OpenaiController":
        @self.router.post(route, summary="Create image", description="Creates an image given a prompt.", tags=self.tags)
        async def generate_image(
            generation_request: Annotated[ImageGenerationRequest, Body],
            user: AuthenticatedUser = Security(self.auth),
        ) -> ImagesResponse:
            return await OpenaiService.generate_image(
                self.image_models, str(generation_request.model), generation_request.model_dump()
            )

        return self

    def stt(self, route: str = "/audio/transcriptions") -> "OpenaiController":
        @self.router.post(
            route, summary="Create transcription", description="Transcribes audio into the input language.", tags=self.tags
        )
        async def create_transcription(
            file: UploadFile = File(..., description="The audio file to transcribe"),
            model: str = Form(..., description="ID of the model to use"),
            language: Optional[str] = Form(None, description="ISO-639-1 language code"),
            prompt: Optional[str] = Form(None, description="Optional text prompt"),
            response_format: Optional[str] = Form("json", description="Format of the response"),
            temperature: Optional[float] = Form(0, description="Sampling temperature between 0 and 1"),
            timestamp_granularities: Optional[List[Literal["word", "segment"]]] = Form(
                None,
                description="Timestamp granularities (e.g. 'word' or 'segment'); only used with verbose_json response_format",
            ),
            user: AuthenticatedUser = Security(self.auth),
        ) -> Transcription | TranscriptionVerbose | str:
            return await OpenaiService.stt(
                self.stt_models,
                file,
                model,
                language,
                prompt,
                response_format,
                temperature,
                timestamp_granularities,
            )

        return self

    def tts(self, route: str = "/audio/speech") -> "OpenaiController":
        @self.router.post(
            route,
            summary="Create speech",
            description="Generates audio from the input text.",
            tags=self.tags
        )
        async def create_speech(
            speech_request: Annotated[TextToSpeechRequest, Body],
            user: AuthenticatedUser = Security(self.auth),
        ) -> StreamingResponse:
            tts_response = await OpenaiService.tts(
                self.tts_models, speech_request.model, speech_request.input, speech_request.model_dump()
            )

            async def stream_generator() -> AsyncIterator[bytes]:
                # Notice we await the aiter_bytes method to get the async iterator.
                async_iterator = await tts_response.aiter_bytes()
                async for chunk in async_iterator:
                    yield chunk

            media_type = tts_response.response.headers.get("Content-Type", f"audio/{speech_request.response_format}")
            return StreamingResponse(stream_generator(), media_type=media_type)

        return self
