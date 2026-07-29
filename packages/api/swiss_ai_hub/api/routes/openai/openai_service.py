import asyncio
import inspect
import io
import logging
import uuid
from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import HTTPException, UploadFile
from nats.aio.client import Client as NATS
from openai import AsyncOpenAI, HttpxBinaryResponseContent
from openai.types import CompletionUsage, ImagesResponse
from openai.types.audio import Transcription, TranscriptionVerbose
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage, ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice as JsonChoice
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
from opentelemetry.propagate import inject
from pydantic import BaseModel
from pydub import AudioSegment
from starlette.responses import StreamingResponse
from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.usage import ResourceType, UsageLimits
from swiss_ai_hub.core.distributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.events.agent.control.exception.exception_event import ExceptionEvent
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.hitl.request.human_in_the_loop_request_event import HumanInTheLoopRequestEvent
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import LiteLLMProxySettings, LiteLLMService, trace_fn
from swiss_ai_hub.core.persistence.utils import str_to_object_id
from swiss_ai_hub.core.routes import ChatService, JsonResources, StreamingResources

from swiss_ai_hub.api.audio.audio_chunking_service import AudioChunkingService, TranscriptionChunk
from swiss_ai_hub.api.routes.agent.agent_service import AgentService
from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest, UserUploadedFile
from swiss_ai_hub.api.routes.openai.dto.embeddings import Embeddings
from swiss_ai_hub.api.routes.openai.dto.embeddings_response import EmbeddingsResponse
from swiss_ai_hub.api.routes.openai.dto.image_generation_request import ImageGenerationRequest
from swiss_ai_hub.api.routes.openai.dto.model_details import ModelDetails
from swiss_ai_hub.api.routes.openai.dto.model_response import ModelResponse
from swiss_ai_hub.api.routes.openai.dto.text_to_speech_request import TextToSpeechRequest
from swiss_ai_hub.api.routes.thread.thread_service import ThreadService

logger = logging.getLogger(__name__)


class OpenaiService:
    """
    A service layer that encapsulates the core operations for generative AI, mirroring OpenAI's API functionality.

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
    @trace_fn
    async def get_models() -> ModelResponse:
        """
        Retrieve the list of available chat models.
        Returns a ModelResponse containing details of every configured chat model.
        """
        chat_model_names = await OpenaiService._model_names_by_type("chat")
        models = [ModelDetails(id=model_name) for model_name in chat_model_names]
        return ModelResponse(data=models)

    @staticmethod
    @trace_fn
    async def get_models_with_assistants(
        *,
        t: LocaleHandler,
    ) -> ModelResponse:
        """
        Retrieve the list of available chat models and assistants.
        Returns a ModelResponse containing details of every configured chat model or assistant.
        """
        model_response = await OpenaiService.get_models()
        chat_models = model_response.data
        agent_instance_dtos = await AgentService.get_all_agent_instances(t, online=True)

        assistants = [
            ModelDetails(
                id=f"{agent_instance_dto.agent_class}/{agent_instance_dto.agent_id}",
                object="assistant",
                agent_class=agent_instance_dto.agent_class,
                agent_id=agent_instance_dto.agent_id,
            )
            for agent_instance_dto in agent_instance_dtos
        ]
        return ModelResponse(data=[*chat_models, *assistants])

    @staticmethod
    @trace_fn
    async def get_model(model_name: str) -> ModelDetails:
        """
        Fetch details for a specific chat model by name.
        Scans the chat model configurations and returns the matching model's details.
        """
        model_response = await OpenaiService.get_models()
        models = [model for model in model_response.data if model.id == model_name]
        if len(models) == 0:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found.")
        return models[0]

    @staticmethod
    @trace_fn
    async def get_model_with_assistants(
        *,
        model_name: str,
        t: LocaleHandler,
    ) -> ModelDetails:
        """
        Fetch details for a specific chat model or ai-hub assistant by name.
        Scans the chat model configurations and returns the matching model's or agent's details.
        """
        try:
            return await OpenaiService.get_model(model_name)
        except HTTPException as model_lookup_error:
            # Only a 404 ("not a known model") should fall through to the agent branch; any other error
            # (e.g. a future 403) must propagate rather than be masked as an assistant lookup.
            if model_lookup_error.status_code != 404:
                raise
        agent_class, agent_id = model_name.split("/")
        agent_dto = await AgentService.get_agent_instance(agent_class, agent_id, t)

        if not agent_dto.is_conversational:
            raise HTTPException(status_code=400, detail="Agent is not a conversational agent.")

        return ModelDetails(
            id=f"{agent_dto.agent_class}/{agent_dto.agent_id}",
            object="assistant",
            agent_class=agent_dto.agent_class,
            agent_id=agent_dto.agent_id,
        )

    @staticmethod
    def _has_model_access(access_checker: AccessChecker, model_name: str) -> bool:
        """Whether the checker grants the ``capability/name`` model. A bare id (no ``/``) forms no valid
        rule, so it is denied rather than raising in the template check. Used to filter model listings."""
        capability, _, name = model_name.partition("/")
        return bool(name) and access_checker.has_access_to_model(capability, name)

    @staticmethod
    def _assert_model_access(user: UserIdentity, model_name: str) -> None:
        """Enforces per-model access for a direct model invocation. Lives on the service, not the
        controller, so internal (non-HTTP) callers cannot bypass it."""
        if not OpenaiService._has_model_access(AccessChecker.from_user(user), model_name):
            raise HTTPException(
                status_code=403, detail=f"User {user.id} does not have permission to access model {model_name}"
            )

    @staticmethod
    @trace_fn
    async def get_embeddings(
        *,
        model_name: str,
        input_text: str | list[str],
        user: UserIdentity,
        dimensions: int | None = None,
        encoding_format: Literal["float", "base64"] | None = None,
    ) -> EmbeddingsResponse:
        """
        Generate text embeddings using the specified embedding model.
        Identifies the model, prepares parameters, and returns embeddings for the input text.
        """
        OpenaiService._assert_model_access(user, model_name)

        embedding_model_names = await OpenaiService._model_names_by_type("embedding", model_name)

        if len(embedding_model_names) == 0:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found.")

        client: AsyncOpenAI = await LiteLLMService.openai_aclient_for_user(user)

        embeddings = await client.embeddings.create(
            input=input_text,
            model=model_name,
            dimensions=dimensions,
            encoding_format=encoding_format,
            user=user.id,
        )
        return EmbeddingsResponse(
            model=model_name,
            data=[Embeddings(index=embedding.index, embedding=embedding.embedding) for embedding in embeddings.data],
        )

    @staticmethod
    @trace_fn
    async def chat_completion(
        *,
        model_name: str,
        chat_completion_request: ChatCompletionRequest,
        user: UserIdentity,
        t: LocaleHandler,
    ) -> ChatCompletion | StreamingResponse:
        """
        Execute a chat completion request with an LLM.
        Delegates to the underlying chat model; supports both synchronous and streaming responses.
        """
        await OpenaiService.get_model(model_name)  # Ensures model exists
        OpenaiService._assert_model_access(user, model_name)
        client: AsyncOpenAI = await LiteLLMService.openai_aclient_for_user(user)

        thread_id, display_id = OpenaiService._extract_thread_and_display_id(chat_completion_request)

        if chat_completion_request.stream:

            async def stream_chat_completion() -> AsyncGenerator[str]:
                """Handles streaming responses from OpenAI's API."""
                kwargs = OpenaiService._filter_kwargs(
                    client.chat.completions.create,
                    chat_completion_request,
                    user=user,
                    locale=t.locale,
                    thread_id=thread_id,
                    display_id=display_id,
                )
                response = await client.chat.completions.create(**kwargs)

                async for chunk in response:
                    yield f"data: {chunk.model_dump_json()}\n\n"
                    await asyncio.sleep(0)

            return StreamingResponse(
                stream_chat_completion(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
                    "X-Accel-Buffering": "no",
                    "Connection": "keep-alive",
                    "Content-Encoding": "identity",
                },
            )
        else:
            kwargs = OpenaiService._filter_kwargs(
                client.chat.completions.create,
                chat_completion_request,
                user=user,
                locale=t.locale,
                thread_id=thread_id,
                display_id=display_id,
            )
            return await client.chat.completions.create(**kwargs)

    @staticmethod
    @trace_fn
    async def chat_completion_with_assistants(
        *,
        model_name: str,
        chat_completion_request: ChatCompletionRequest,
        user: UserIdentity,
        nc: NATS,
        usage_limits: UsageLimits,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        t: LocaleHandler,
        aihub_headers: dict[str, str] | None = None,
    ) -> ChatCompletion | StreamingResponse:
        """
        Execute a chat completion request with an LLM or an assistant.
        Delegates to the underlying chat model; supports both synchronous and streaming responses.
        """
        try:
            return await OpenaiService.chat_completion(
                model_name=model_name,
                chat_completion_request=chat_completion_request,
                user=user,
                t=t,
            )
        except HTTPException as e:
            if e.status_code != 404:
                raise

        agent_class, agent_id = model_name.split("/")
        if not AccessChecker.from_user(user).has_access_to_agent(agent_class, agent_id):
            raise HTTPException(
                status_code=403,
                detail=f"User {user.id} does not have permission to access assistant {model_name}",
            )

        agent_dto = await AgentService.get_agent_instance(agent_class, agent_id, t)

        if not agent_dto.is_conversational:
            raise HTTPException(status_code=400, detail="Agent is not a conversational agent.")

        if chat_completion_request.stream:
            return await OpenaiService.stream_assistant(
                agent_class=agent_class,
                agent_id=agent_id,
                chat_completion_request=chat_completion_request,
                user=user,
                nc=nc,
                usage_limits=usage_limits,
                external_agent_event_distributor=external_agent_event_distributor,
                locale=t.locale,
                aihub_headers=aihub_headers,
            )

        return await OpenaiService.json_assistant(
            agent_class=agent_class,
            agent_id=agent_id,
            chat_completion_request=chat_completion_request,
            user=user,
            nc=nc,
            usage_limits=usage_limits,
            external_agent_event_distributor=external_agent_event_distributor,
            locale=t.locale,
            aihub_headers=aihub_headers,
        )

    @staticmethod
    @trace_fn
    async def json_assistant(
        *,
        agent_class: str,
        agent_id: str,
        chat_completion_request: ChatCompletionRequest,
        user: UserIdentity,
        nc: NATS,
        usage_limits: UsageLimits,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        locale: str | None = None,
        aihub_headers: dict[str, str] | None = None,
    ):
        thread_id, display_id = OpenaiService._extract_thread_and_display_id(chat_completion_request)
        if thread_id and chat_completion_request.metadata.reconstruct_history:
            chat_completion_request.messages = await OpenaiService._reconstruct_history(
                chat_completion_request, thread_id
            )
        files = OpenaiService._extract_files(chat_completion_request)

        await usage_limits.check_and_raise(user, ResourceType.AGENT, agent_class, agent_id, locale=locale)

        resources: JsonResources = await ChatService.start_json_chat_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completion_request.llama_index_messages,
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
            thread_id=str_to_object_id(thread_id),
            display_id=str_to_object_id(display_id),
            files=files,
            locale=locale,
            aihub_headers=aihub_headers,
        )
        # Wait until all events are processed, draining trailing events before teardown
        await ChatService.wait_for_stop_then_drain(resources)

        if resources.stop_event.is_exception_event:
            raise HTTPException(resources.stop_event.http_status_code, resources.stop_event.message)

        # Construct final JSON response
        chat_content = ChatService.build_json_response_content(resources.chunk_events, resources.stop_event)
        return ChatCompletion(
            id=str(uuid.uuid4()),
            object="chat.completion",
            created=int(datetime.now(UTC).timestamp()),
            model=resources.model_name,
            choices=[
                JsonChoice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=chat_content.content,
                    ),
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
    @trace_fn
    async def stream_assistant(
        *,
        agent_class: str,
        agent_id: str,
        chat_completion_request: ChatCompletionRequest,
        user: UserIdentity,
        nc: NATS,
        usage_limits: UsageLimits,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        locale: str | None = None,
        aihub_headers: dict[str, str] | None = None,
    ):
        thread_id, display_id = OpenaiService._extract_thread_and_display_id(chat_completion_request)
        if thread_id and chat_completion_request.metadata.reconstruct_history:
            chat_completion_request.messages = await OpenaiService._reconstruct_history(
                chat_completion_request, thread_id
            )
        files = OpenaiService._extract_files(chat_completion_request)

        await usage_limits.check_and_raise(user, ResourceType.AGENT, agent_class, agent_id, locale=locale)

        resources: StreamingResources = await ChatService.start_stream_chat_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completion_request.llama_index_messages,
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
            thread_id=str_to_object_id(thread_id),
            display_id=str_to_object_id(display_id),
            files=files,
            locale=locale,
            aihub_headers=aihub_headers,
        )

        return StreamingResponse(
            OpenaiService._sse_event_generator(resources),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
                "Content-Encoding": "identity",
            },
        )

    @staticmethod
    async def _sse_event_generator(resources: StreamingResources) -> AsyncGenerator[str]:
        streamed_parts: list[str] = []
        async for chunk_event in ChatService.iter_streamed_display_events(resources):
            streamed_parts.append(chunk_event.content)
            yield OpenaiService._build_chunk_sse(content=chunk_event.content, model=chunk_event.model_name)

        yield OpenaiService._build_chunk_sse(
            content=OpenaiService._resolve_final_content(resources.stop_event, streamed="".join(streamed_parts)),
            model="",
            finish_reason="stop",
        )

    @staticmethod
    def _resolve_final_content(
        stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent | None,
        streamed: str = "",
    ) -> str:
        if stop_event.is_hitl_request_event:
            return stop_event.question
        if stop_event.is_exception_event:
            return f"\n\n>[!CAUTION]\n>**Error:** {stop_event.message}\n"
        # Backstop: emit only the portion of the authoritative answer the client never received, in case
        # chunks were lost to the stop-vs-chunk dispatch race. Empty once everything has already streamed.
        # Best-effort: the prefix match can miss if the stream parser normalized whitespace differently
        # from output_messages, in which case we keep what streamed rather than risk duplicating it.
        output_messages = getattr(stop_event, "output_messages", None) or []
        full_answer = (output_messages[-1].content or "") if output_messages else ""
        if full_answer and full_answer.startswith(streamed):
            return full_answer[len(streamed) :]
        return "" if streamed else full_answer

    @staticmethod
    def _build_chunk_sse(*, content: str, model: str, finish_reason: str | None = None) -> str:
        chunk = ChatCompletionChunk(
            id=str(uuid.uuid4()),
            object="chat.completion.chunk",
            created=int(datetime.now(UTC).timestamp()),
            model=model,
            choices=[
                Choice(
                    index=0,
                    delta=ChoiceDelta(content=content, role="assistant"),
                    finish_reason=finish_reason,
                ),
            ],
            usage=None,
        )
        return f"data: {chunk.model_dump_json()}\n\n"

    @staticmethod
    @trace_fn
    async def generate_image(
        *,
        model_name: str,
        image_generation_request: ImageGenerationRequest,
        user: UserIdentity,
    ) -> ImagesResponse:
        """
        Generate an image using the specified image model.
        Routes the generation request to the corresponding Azure image model client.
        """
        OpenaiService._assert_model_access(user, model_name)

        image_model_names = await OpenaiService._model_names_by_type("image_generation", model_name)
        if len(image_model_names) == 0:
            raise ValueError(f"Model {model_name} not found.")

        client: AsyncOpenAI = await LiteLLMService.openai_aclient_for_user(user)
        kwargs = OpenaiService._filter_kwargs(client.images.generate, image_generation_request, user=user)
        return await client.images.generate(**kwargs)

    @staticmethod
    @trace_fn
    async def stt(
        *,
        model_name: str,
        file: UploadFile,
        user: UserIdentity,
        language: str | None,
        prompt: str | None,
        response_format: str | None,
        temperature: float | None,
        timestamp_granularities: list[Literal["word", "segment"]] | None,
    ) -> Transcription | TranscriptionVerbose | str:
        """
        Transcribe an audio file to text.
        Utilizes the specified speech-to-text model and parameters to convert audio into transcription.
        Handles chunking of large audio files to comply with API size limits.
        """
        OpenaiService._assert_model_access(user, f"transcription/{model_name}")

        tts_model_names = await OpenaiService._model_names_by_type("audio_transcription", model_name)
        if len(tts_model_names) == 0:
            raise ValueError(f"Model {model_name} not found.")

        client: AsyncOpenAI = await LiteLLMService.openai_aclient_for_user(user)

        file_ext = file.filename.rsplit(".", 1)[-1].lower()
        audio = AudioSegment.from_file(file.file, format=file_ext)
        audio_chunks: list[AudioSegment] = await AudioChunkingService.chunk_audio(audio)
        transcription_chunks: list[TranscriptionChunk] = []

        for i, audio_chunk in enumerate(audio_chunks):
            buffer = io.BytesIO()
            audio_chunk.export(buffer, format="wav")
            filename_without_ext = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
            wav_filename = f"{filename_without_ext}_chunk{i}.wav"
            file_tuple = (wav_filename, buffer, "audio/wav")

            result: TranscriptionChunk = await client.audio.transcriptions.create(
                model=model_name,
                file=file_tuple,
                language=language,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                timestamp_granularities=timestamp_granularities,
            )

            transcription_chunks.append(result)

        merged_text: str = AudioChunkingService.merge_transcriptions(transcription_chunks)

        if response_format == "text":
            return merged_text
        elif response_format == "srt" or response_format == "vtt":
            logger.warning(f"Format {response_format} not fully supported with chunking, returning as text")
            return merged_text
        elif response_format == "verbose_json":
            return TranscriptionVerbose(
                text=merged_text,
                language=language,
                duration=len(audio) / 1000,  # Convert milliseconds to seconds
                segments=[],
                words=[],
            )
        else:
            return Transcription(text=merged_text)

    @staticmethod
    @trace_fn
    async def tts(
        *,
        model_name: str,
        input_text: str,
        tts_request: TextToSpeechRequest,
        user: UserIdentity,
    ) -> HttpxBinaryResponseContent:
        """
        Convert text to speech and return the audio content.
        Sends a TTS request to the designated model and streams the resulting audio bytes.
        """
        OpenaiService._assert_model_access(user, f"speech/{model_name}")

        tts_model_names = await OpenaiService._model_names_by_type("audio_speech", model_name)
        if len(tts_model_names) == 0:
            raise ValueError(f"Model {model_name} not found.")

        client: AsyncOpenAI = await LiteLLMService.openai_aclient_for_user(user)
        kwargs = OpenaiService._filter_kwargs(client.audio.speech.create, tts_request)

        return await client.audio.speech.create(input=input_text, **kwargs)

    @staticmethod
    def _extract_thread_and_display_id(
        chat_completion_request: ChatCompletionRequest,
    ) -> tuple[str | None, str | None]:
        thread_id = chat_completion_request.metadata.thread_id if chat_completion_request.metadata else None
        display_id = chat_completion_request.metadata.display_id if chat_completion_request.metadata else None
        return thread_id, display_id

    @staticmethod
    def _extract_files(
        chat_completion_request: ChatCompletionRequest,
    ) -> list[UserUploadedFile] | None:
        return chat_completion_request.metadata.files if chat_completion_request.metadata else None

    @staticmethod
    async def _reconstruct_history(
        chat_completion_request: ChatCompletionRequest, thread_id: str
    ) -> list[ChatCompletionMessageParam]:
        history = await ThreadService.thread_as_message_history(thread_id)
        user_message = chat_completion_request.messages[-1]
        return history.messages + [user_message]

    @staticmethod
    def _filter_kwargs(
        sdk_fn: Callable,
        fn_kwargs_model: BaseModel,
        user: UserIdentity | None = None,
        thread_id: str | None = None,
        display_id: str | None = None,
        locale: str | None = None,
    ) -> dict[str, Any]:
        """
        Wraps an SDK client's `chat.completions.create` method, intelligently preparing
        arguments from a Pydantic model instance.
        """
        sdk_method_signature = inspect.signature(sdk_fn)
        sdk_known_param_names = set(sdk_method_signature.parameters.keys())
        payload_dict = fn_kwargs_model.model_dump(exclude_unset=True)
        payload_dict["user"] = user.id

        sdk_call_kwargs: dict[str, Any] = {}

        for key, value in payload_dict.items():
            if key in sdk_known_param_names and key != "metadata":
                sdk_call_kwargs[key] = value

        metadata_tags = [
            f"{key}:{value}" for key, value in [("thread_id", thread_id), ("display_id", display_id)] if value
        ]

        sdk_call_kwargs["extra_body"] = {
            "litellm_session_id": thread_id,
            "guardrail_config": {"language": locale},
            "metadata": {"tags": metadata_tags},
        }
        sdk_call_kwargs["extra_headers"] = {}
        inject(sdk_call_kwargs["extra_headers"])

        return sdk_call_kwargs

    @staticmethod
    async def _model_names_by_type(
        model_type: Literal["chat", "embedding", "image_generation"], model_name: str | None = None
    ) -> list[str]:
        async with LiteLLMProxySettings().httpx_aclient as litellm_client:
            models = await litellm_client.get("/v1/model/info")
        candidates = [
            model["model_name"] for model in models.json()["data"] if model["model_info"]["mode"] == model_type
        ]
        return [name for name in candidates if not model_name or model_name == name]
