import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, List, Literal, Optional, Tuple

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.resources.models.image.azure.AzureImageModelConfig import AzureOpenaiImageModelConfig
from aihub_lib.generative_ai.resources.models.llm.chat.ChatLLMConfig import ChatLLMConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.EmbeddingLLMConfig import EmbeddingLLMConfig
from aihub_lib.generative_ai.resources.models.stt.azure.AzureSTTConfig import AzureOpenaiSTTConfig
from aihub_lib.generative_ai.resources.models.tts.azure.AzureTTSConfig import AzureOpenaiTTSConfig
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from fastapi import HTTPException, UploadFile
from nats.aio.client import Client as NATS
from openai import AsyncAzureOpenAI, AsyncOpenAI, HttpxBinaryResponseContent
from openai.types import CompletionUsage, FileContent, ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice as JsonChoice
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
from starlette.responses import StreamingResponse

from aihub_api.routes.agent.AgentService import AgentService
from aihub_api.routes.openai.dto.ChatCompletionRequest import ChatCompletionRequest
from aihub_api.routes.openai.dto.Embeddings import Embeddings
from aihub_api.routes.openai.dto.EmbeddingsResponse import EmbeddingsResponse
from aihub_api.routes.openai.dto.ModelDetails import ModelDetails
from aihub_api.routes.openai.dto.ModelResponse import ModelResponse

logger = logging.getLogger(__name__)


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
    async def get_models_with_assistants(
        chat_models: List[ChatLLMConfig], user: AuthenticatedUser, nc: NATS
    ) -> ModelResponse:
        """
        Retrieve the list of available chat models and assistants available through NATs
        Returns a ModelResponse containing details of every configured chat model or assistant.
        """
        chat_models = [ModelDetails(id=model.name) for model in chat_models]
        agent_dtos = await AgentService.discover_agents(nc)
        agent_dtos = [
            agent_dto
            for agent_dto in agent_dtos
            if (agent_dto.is_conversational and user.has_access_to_agent(agent_dto.agent_class, agent_dto.agent_id))
        ]
        assistants = [
            ModelDetails(id=f"{agent_dto.agent_class}/{agent_dto.agent_id}", object="assistant")
            for agent_dto in agent_dtos
        ]
        return ModelResponse(data=[*chat_models, *assistants])

    @staticmethod
    def get_model(chat_models: List[ChatLLMConfig], model_name: str) -> ModelDetails:
        """
        Fetch details for a specific chat model by name.
        Scans the chat model configurations and returns the matching model's details.
        """
        models = [ModelDetails(id=model.name) for model in chat_models if model.name == model_name]
        if len(models) == 0:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found.")
        return models[0]

    @staticmethod
    async def get_model_with_assistants(
        chat_models: List[ChatLLMConfig], model_name: str, user: AuthenticatedUser, nc: NATS
    ) -> ModelDetails:
        """
        Fetch details for a specific chat model or ai-hub assistant by name.
        Scans the chat model configurations and returns the matching model's or agent's details.
        """
        try:
            return OpenaiService.get_model(chat_models, model_name)
        except HTTPException:
            pass
        agent_class, agent_id = model_name.split("/")
        agent_dto = await AgentService.get_agent(nc, agent_class, agent_id)
        if not agent_dto.is_conversational:
            raise HTTPException(status_code=400, detail="Agent is not a conversational agent.")
        if not user.has_access_to_agent(agent_class, agent_id):
            raise HTTPException(status_code=403, detail="User does not have access to this agent.")
        return ModelDetails(id=f"{agent_dto.agent_class}/{agent_dto.agent_id}", object="assistant")

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
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found.")
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
        Execute a chat completion request with an LLM.
        Delegates to the underlying chat model; supports both synchronous and streaming responses.
        """
        models = [model for model in chat_models if model.name == model_name]
        if len(models) == 0:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found.")
        chat_model_config = models[0]

        chat_model, _ = chat_model_config.to_llama_index()
        client: AsyncOpenAI | AsyncAzureOpenAI = chat_model._get_aclient()

        del function_args["chat_id"]
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
    async def chat_completion_with_assistants(
        chat_models: List[ChatLLMConfig],
        model_name: str,
        chat_completion_request: ChatCompletionRequest,
        user: AuthenticatedUser,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> ChatCompletion | StreamingResponse:
        """
        Execute a chat completion request with an LLM or an assistant.
        Delegates to the underlying chat model; supports both synchronous and streaming responses.
        """
        models = [model for model in chat_models if model.name == model_name]
        if len(models) > 0:
            return await OpenaiService.chat_completion(chat_models, model_name, chat_completion_request.model_dump())

        agent_class, agent_id = model_name.split("/")

        if not user.has_access_to_agent(agent_class, agent_id):
            raise HTTPException(status_code=403, detail="User does not have access to this agent.")

        agent_dto = await AgentService.get_agent(nc, agent_class, agent_id)

        if not agent_dto.is_conversational:
            raise HTTPException(status_code=400, detail="Agent is not a conversational agent.")

        if chat_completion_request.stream:
            return await OpenaiService.stream_assistant(
                agent_class, agent_id, chat_completion_request, user, nc, ws_receiver
            )

        return await OpenaiService.json_assistant(agent_class, agent_id, chat_completion_request, user, nc, ws_receiver)

    @staticmethod
    async def json_assistant(
        agent_class: str,
        agent_id: str,
        chat_completion_request: ChatCompletionRequest,
        user: AuthenticatedUser,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ):
        resources: JsonResources = await ChatService.start_json_chat_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completion_request.messages,
            nc=nc,
            ws_receiver=ws_receiver,
            thread_id=ThreadEntity.to_thread_id(chat_completion_request.chat_id),
        )
        # Wait until all events are processed
        await resources.stop_signal.wait()
        await resources.subscriber.stop()

        # Construct final JSON response
        content = ChatService.build_json_response_content(resources.chunk_events, resources.stop_event)
        return ChatCompletion(
            id=str(uuid.uuid4()),
            object="chat.completion",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=resources.model_name,
            choices=[
                JsonChoice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=resources.costs.prompt_token_count,
                completion_tokens=resources.costs.completion_token_count,
                total_tokens=(resources.costs.prompt_token_count + resources.costs.completion_token_count),
            ),
        )

    @staticmethod
    async def stream_assistant(
        agent_class: str,
        agent_id: str,
        chat_completion_request: ChatCompletionRequest,
        user: AuthenticatedUser,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ):
        resources: StreamingResources = await ChatService.start_stream_chat_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completion_request.messages,
            nc=nc,
            ws_receiver=ws_receiver,
            thread_id=ThreadEntity.to_thread_id(chat_completion_request.chat_id),
        )

        async def sse_event_generator():
            while True:
                if resources.stop_signal.is_set() and resources.chunk_queue.empty():
                    logger.debug("Stop streaming due to stop_event and empty queue")
                    break
                try:
                    chunk_event = await asyncio.wait_for(resources.chunk_queue.get(), timeout=0.5)
                    chat_completion_chunk = ChatCompletionChunk(
                        id=str(uuid.uuid4()),
                        object="chat.completion.chunk",
                        created=int(datetime.now(timezone.utc).timestamp()),
                        model=chunk_event.model_name,
                        choices=[Choice(index=0, delta=ChoiceDelta(content=chunk_event.content, role="assistant"))],
                        usage=None,
                    )
                    yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"
                    resources.chunk_queue.task_done()
                except asyncio.TimeoutError:
                    # No new chunk yet; keep waiting
                    continue
                except asyncio.CancelledError:
                    break

            # Send a final "stop" chunk at the end
            if resources.stop_event.is_hitl_request_event:
                content = resources.stop_event.question
            else:
                content = ""
            chat_completion_chunk = ChatCompletionChunk(
                id=str(uuid.uuid4()),
                object="chat.completion.chunk",
                created=int(datetime.now(timezone.utc).timestamp()),
                model="",
                choices=[Choice(index=0, delta=ChoiceDelta(content=content, role="assistant"), finish_reason="stop")],
                usage=None,
            )
            yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"

        return StreamingResponse(
            sse_event_generator(),
            media_type="text/event-stream",
        )

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
