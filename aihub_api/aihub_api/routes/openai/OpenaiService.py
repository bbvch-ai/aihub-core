import asyncio
from typing import AsyncGenerator, Dict, List, Literal, Mapping, Optional, Tuple

from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from fastapi import UploadFile
from openai import AsyncAzureOpenAI, AsyncOpenAI, HttpxBinaryResponseContent
from openai.types import FileContent, ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose
from openai.types.chat import ChatCompletion
from starlette.responses import StreamingResponse

from aihub_api.routes.openai.dto.Embeddings import Embeddings
from aihub_api.routes.openai.dto.EmbeddingsResponse import EmbeddingsResponse
from aihub_api.routes.openai.dto.ModelDetails import ModelDetails
from aihub_api.routes.openai.dto.ModelResponse import ModelResponse


class OpenaiService:
    """
    A service layer that encapsulates the core operations for generative AI, mirroring OpenAI's API functionality.

    ### Purpose
    OpenaiService provides the business logic for:
    - Retrieving and detailing available AI models.
    - Generating text embeddings.
    - Handling chat completions, supporting both standard and streaming responses.
    - Creating images based on textual prompts.
    - Converting audio files into text (STT) and text into speech (TTS).

    By abstracting these operations, the service ensures consistency with OpenAI's API semantics,
    allowing the underlying implementation to be used seamlessly by the OpenaiController.
    """

    @staticmethod
    def get_models(chat_models: List[ChatLLMConfig]) -> ModelResponse:
        """
        Retrieve the list of available chat models.
        Returns a ModelResponse containing details of every configured chat model.
        """
        models = [ModelDetails(id=model.name) for model in chat_models]
        return ModelResponse(data=models)

    @staticmethod
    def get_model(chat_models: List[ChatLLMConfig], model_name: str) -> ModelDetails:
        """
        Fetch details for a specific chat model by name.
        Scans the chat model configurations and returns the matching model's details.
        """
        models = [ModelDetails(id=model.name) for model in chat_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")
        return models[0]

    @staticmethod
    def get_embeddings(
        embedding_models: List[EmbeddingLLMConfig],
        model_name: str,
        input_text: str | List[str],
        dimensions: Optional[int] = None,
        encoding_format: Optional[str] = None,
    ) -> EmbeddingsResponse:
        """
        Generate text embeddings using the specified embedding model.
        Identifies the model, prepares parameters, and returns embeddings for the input text.
        """
        models = [model for model in embedding_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")
        embedding_model_config = models[0]

        model_parameters = None
        if isinstance(embedding_model_config, AzureOpenAIEmbeddingConfig):
            model_parameters = AzureOpenAIEmbeddingParameter(
                dimensions=dimensions or embedding_model_config.default_parameter.dimensions,
                encoding_format=encoding_format or embedding_model_config.default_parameter.encoding_format,
            )
        embedding_model, _ = embedding_model_config.to_llama_index(model_parameter=model_parameters)
        inputs = input_text if isinstance(input_text, list) else [input_text]
        embeddings = embedding_model.get_text_embedding_batch(inputs)
        return EmbeddingsResponse(
            model=model_name,
            data=[Embeddings(index=i, embedding=embedding) for i, embedding in enumerate(embeddings)],
        )

    @staticmethod
    async def chat_completion(
        chat_models: List[ChatLLMConfig], model_name: str, function_args: Dict
    ) -> ChatCompletion | StreamingResponse:
        """
        Execute a chat completion request.
        Delegates to the underlying chat model; supports both synchronous and streaming responses.
        """
        models = [model for model in chat_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")
        chat_model_config = models[0]

        chat_model, _ = chat_model_config.to_llama_index()
        client: AsyncOpenAI | AsyncAzureOpenAI = chat_model._get_aclient()

        if function_args.get("stream", False):

            async def stream_chat_completion(**kwargs) -> AsyncGenerator[str, None]:
                """Handles streaming responses from OpenAI's API."""
                response = await client.chat.completions.create(**kwargs)

                async for chunk in response:
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0)

            return StreamingResponse(stream_chat_completion(**function_args), media_type="text/event-stream")
        else:
            return await client.chat.completions.create(**function_args)

    @staticmethod
    async def generate_image(
        image_models: List[AzureOpenaiImageModelConfig], model_name: str, function_args: Dict
    ) -> ImagesResponse:
        """
        Generate an image using the specified image model.
        Routes the generation request to the corresponding Azure image model client.
        """
        models = [model for model in image_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")
        image_model_config = models[0]
        client: AsyncOpenAI | AsyncAzureOpenAI = image_model_config.get_openai_client()
        return await client.images.generate(**function_args)

    @staticmethod
    async def stt(
        stt_models: List[AzureOpenaiSTTConfig],
        file: UploadFile,
        model_name: str,
        language: Optional[str],
        prompt: Optional[str],
        response_format: Optional[str],
        temperature: Optional[float],
        timestamp_granularities: Optional[List[Literal["word", "segment"]]],
    ) -> Transcription | TranscriptionVerbose | str:
        """
        Transcribe an audio file to text.
        Utilizes the specified speech-to-text model and parameters to convert audio into transcription.
        """
        models = [model for model in stt_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")

        stt_model_config = models[0]
        client: AsyncOpenAI | AsyncAzureOpenAI = stt_model_config.get_openai_client()

        file_tuple: Tuple[Optional[str], FileContent, Optional[str]] = (
            file.filename,
            file.file,
            file.content_type,
        )

        return await client.audio.transcriptions.create(
            model=model_name,
            file=file_tuple,
            language=language,
            prompt=prompt,
            response_format=response_format,
            temperature=temperature,
            timestamp_granularities=timestamp_granularities,
        )

    @staticmethod
    async def tts(
        tts_models: List[AzureOpenaiTTSConfig],
        model_name: str,
        input_text: str,
        function_args: Dict,
    ) -> HttpxBinaryResponseContent:
        """
        Convert text to speech and return the audio content.
        Sends a TTS request to the designated model and streams the resulting audio bytes.
        """
        models = [model for model in tts_models if model.name == model_name]
        if len(models) == 0:
            raise ValueError(f"Model {model_name} not found.")

        tts_model_config = models[0]
        client: AsyncOpenAI | AsyncAzureOpenAI = tts_model_config.get_openai_client()
        return await client.audio.speech.create(**function_args)
