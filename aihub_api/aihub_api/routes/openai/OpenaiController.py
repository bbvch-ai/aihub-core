import logging
from typing import Annotated, Any, Callable, List, Optional, Literal, AsyncIterator

from openai.types import ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from fastapi import Body, Depends, File, UploadFile, Form
from llama_index.llms.openai import OpenAI
from openai.types.chat import ChatCompletion
from starlette.responses import StreamingResponse

from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureTTSConfig
from aihub_lib.routes.Controller import Controller
from .OpenaiService import OpenaiService
from .dto.ChatCompletionRequest import ChatCompletionRequest
from .dto.EmbeddingsRequest import EmbeddingsRequest
from .dto.EmbeddingsResponse import EmbeddingsResponse
from .dto.ImageGenerationRequest import ImageGenerationRequest
from .dto.ModelDetails import ModelDetails
from .dto.ModelResponse import ModelResponse
from .dto.TextToSpeechRequest import TextToSpeechRequest

logger = logging.getLogger(__name__)


class OpenaiController(Controller):
    def __init__(
        self,
        route: str = "/openai",
        auth: Callable[..., Any] = None,
        embedding_models: List[EmbeddingLLMConfig] = None,
        chat_models: List[ChatLLMConfig] = None,
        image_models: List[AzureImageModelConfig] = None,
        stt_models: List[AzureSTTConfig] = None,
        tts_models: List[AzureTTSConfig] = None,
    ):
        super().__init__(route, auth)
        self.embedding_models = embedding_models or []
        self.chat_models = chat_models or []
        self.image_models = image_models or []
        self.tts_models = tts_models or []
        self.stt_models = stt_models or []

        for chat_model in self.chat_models:
            model, _ = chat_model.to_llama_index()
            if not isinstance(model, OpenAI):
                raise ValueError(f"Chat model {chat_model.name} is not an OpenAI compatible model.")

    def get_models(self, route: str = "/models") -> "OpenaiController":
        @self.router.get(route)
        async def get_models(
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ModelResponse:
            return OpenaiService.get_models(self.chat_models)

        return self

    def get_model(self, route: str = "/models/{full_path:path}") -> "OpenaiController":
        @self.router.get(route)
        async def get_model(
            full_path: str,
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ModelDetails:
            return OpenaiService.get_model(self.chat_models, model_name=full_path)

        return self

    def get_embeddings(self, route: str = "/embeddings") -> "OpenaiController":
        @self.router.post(route)
        async def get_embeddings(
            req: Annotated[EmbeddingsRequest, Body],
            user: AuthenticatedUser = Depends(self.auth),
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
        @self.router.post(route, response_model=ChatCompletion)
        async def chat_completion(
            completion_request: Annotated[ChatCompletionRequest, Body],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ChatCompletion | StreamingResponse:
            return await OpenaiService.chat_completion(
                self.chat_models, completion_request.model, completion_request.model_dump()
            )

        return self

    def generate_image(self, route: str = "/images/generations") -> "OpenaiController":
        @self.router.post(route)
        async def generate_image(
            generation_request: Annotated[ImageGenerationRequest, Body],
            user: AuthenticatedUser = Depends(self.auth),
        ) -> ImagesResponse:
            return await OpenaiService.generate_image(
                self.image_models, str(generation_request.model), generation_request.model_dump()
            )

        return self

    def stt(self, route: str = "/audio/transcriptions") -> "OpenaiController":
        @self.router.post(route)
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
            user: AuthenticatedUser = Depends(self.auth),
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
        @self.router.post(route)
        async def create_speech(
            speech_request: Annotated[TextToSpeechRequest, Body],
            user: AuthenticatedUser = Depends(self.auth),
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
