import mimetypes
from collections.abc import Iterable
from typing import Annotated, Any, Literal

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from llama_index.core.base.llms.types import ChatMessage, ContentBlock, ImageBlock, MessageRole, TextBlock
from openai.types import ChatModel
from openai.types.chat import (
    ChatCompletionAudioParam,
    ChatCompletionMessageParam,
    ChatCompletionModality,
    ChatCompletionPredictionContentParam,
    ChatCompletionReasoningEffort,
    ChatCompletionStreamOptionsParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    completion_create_params,
)
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, ValidationError
from swiss_ai_hub.core.events.agent import ChatFeature, InlineFile, UserUploadedFile


def _resolve_dict_part(part: dict[str, Any]) -> dict[str, Any] | None:
    part_type = part.get("type")
    if part_type == "text":
        return {"type": "text", "text": part.get("text", "")}
    if part_type == "image_url":
        return {"type": "image_url", "image_url": part.get("image_url", {})}
    if part_type == "file":
        return {"type": "file", "file": part.get("file", {})}
    return None


def _resolve_content_part(part: Any) -> dict[str, Any] | None:
    if isinstance(part, dict):
        return _resolve_dict_part(part)
    if hasattr(part, "dict"):
        return part.dict()
    try:
        return dict(part)
    except Exception:
        return None


def resolve_message_content(message: dict[str, Any]) -> dict[str, Any]:
    """
    Resolves the content field in a message, handling ValidatorIterator instances.
    Returns a new message dict with properly resolved content.
    """
    if "content" not in message:
        return message

    content = message["content"]

    if isinstance(content, str) or not isinstance(content, Iterable):
        return message

    resolved_content = [resolved for resolved in (_resolve_content_part(p) for p in content) if resolved is not None]
    new_message = message.copy()
    new_message["content"] = resolved_content
    return new_message


def _image_part_to_block(part: dict[str, Any]) -> ImageBlock | None:
    image_url = part.get("image_url", {})
    if not isinstance(image_url, dict) or "url" not in image_url:
        return None
    return ImageBlock(url=image_url.get("url"), detail=image_url.get("detail", "auto"))


def _content_part_to_block(part: Any) -> ContentBlock | None:
    if not isinstance(part, dict):
        return None
    part_type = part.get("type")
    if part_type == "text":
        return TextBlock(text=part.get("text", ""))
    if part_type == "image_url":
        return _image_part_to_block(part)
    return None


def _content_to_blocks(content: Any) -> list[ContentBlock]:
    if isinstance(content, str):
        return [TextBlock(text=content)]
    if not isinstance(content, Iterable) or isinstance(content, str | bytes):
        return []
    return [block for block in (_content_part_to_block(p) for p in content) if block is not None]


def openai_message_to_llama_index(message: dict[str, Any]) -> ChatMessage:
    """
    Converts an OpenAI message dict to a llama-index ChatMessage.
    Handles both simple string content and complex multimodal content.
    """
    message = resolve_message_content(message)

    role = message.get("role", "user")
    blocks = _content_to_blocks(message.get("content"))
    additional_kwargs = {k: v for k, v in message.items() if k not in ["role", "content"]}

    return ChatMessage(role=MessageRole(role), blocks=blocks, additional_kwargs=additional_kwargs)


class Metadata(BaseModel):
    thread_id: Annotated[
        str | None, Field(description="Provide thread ID to continue conversation in an existing thread.")
    ] = None
    display_id: Annotated[str | None, Field(description="Gives control over display ID used for this run.")] = None
    reconstruct_history: Annotated[
        bool | None,
        Field(
            description="When set to True, message set on UserMessageEvent "
            "will be calculated based on thread event history"
        ),
    ] = None
    files: Annotated[
        list[UserUploadedFile] | None,
        Field(description="List of files to attach to the request, if supported by the model."),
    ] = None
    features: Annotated[
        list[ChatFeature],
        Field(
            description="Chat features requested for this message (e.g. web_search). The agent serves those its "
            "blueprint supports and ignores the rest."
        ),
    ] = []


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: Annotated[
        list[ChatCompletionMessageParam] | None, Field(description="Messages to complete the chat with.")
    ]
    model: Annotated[str | ChatModel, Field(description="ID of the model to use for the chat completion.")]
    stream: Annotated[bool, Field(description="Enable streaming response.")] = False

    user: str | None = None

    audio: ChatCompletionAudioParam | None = None
    frequency_penalty: float | None = None
    function_call: completion_create_params.FunctionCall | None = None
    functions: Iterable[completion_create_params.Function] | None = None
    logit_bias: dict[str, int] | None = None
    logprobs: bool | None = None
    max_completion_tokens: int | None = None
    max_tokens: int | None = None
    metadata: Metadata | None = None
    modalities: list[ChatCompletionModality] | None = None
    n: int | None = None
    parallel_tool_calls: bool | None = None
    prediction: ChatCompletionPredictionContentParam | None = None
    presence_penalty: float | None = None
    reasoning_effort: ChatCompletionReasoningEffort | None = None
    response_format: completion_create_params.ResponseFormat | None = None
    seed: int | None = None
    service_tier: Literal["auto", "default", "flex", "scale", "priority"] | None = None
    stop: str | None | list[str] = None
    store: bool | None = None
    stream_options: ChatCompletionStreamOptionsParam | None = None
    temperature: float | None = None
    tool_choice: ChatCompletionToolChoiceOptionParam | None = None
    tools: Iterable[ChatCompletionToolParam] | None = None
    top_logprobs: int | None = None
    top_p: float | None = None

    _message_dicts: list[dict[str, Any]] | None = PrivateAttr(None)

    def message_dicts(self) -> list[dict[str, Any]]:
        """The messages with every content read once and kept: pydantic hands list contents over as one-shot
        iterators, and the files, the images and the conversion to llama-index messages each read them."""
        if self._message_dicts is None:
            self._message_dicts = [
                {**message, "content": list(message["content"])}
                if not isinstance(message.get("content"), str | None)
                else dict(message)
                for message in self.messages or []
            ]
        return self._message_dicts

    def inline_files(self) -> list[InlineFile]:
        """The files sent as `file` content parts of the last user message, the one this turn answers.

        Earlier messages are history: their files were attached on their own turn, and with `reconstruct_history`
        the API discards them anyway.
        """
        user_messages = [message for message in self.message_dicts() if message.get("role") == "user"]
        if not user_messages:
            return []
        message = user_messages[-1]
        content = message.get("content")
        if isinstance(content, str) or content is None:
            return []
        return [
            ChatCompletionRequest._inline_file(part.get("file", {}))
            for part in content
            if isinstance(part, dict) and part.get("type") == "file"
        ]

    @staticmethod
    def _inline_file(file: dict[str, Any]) -> InlineFile:
        file_data, filename = file.get("file_data"), file.get("filename")
        if not file_data or not filename:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "A file content part needs file_data and filename. References to files hosted by OpenAI (file_id) "
                "are not supported.",
            )
        header, separator, content = file_data.partition(",")
        if separator and header.startswith("data:") and header.endswith(";base64"):
            file_type = header.removeprefix("data:").removesuffix(";base64")
        else:
            content, file_type = file_data, mimetypes.guess_type(filename)[0] or "application/octet-stream"
        try:
            return InlineFile(filename=filename, file_type=file_type, content=content)
        except ValidationError as validation_error:
            raise RequestValidationError(validation_error.errors(include_url=False)) from validation_error

    @property
    def llama_index_messages(self) -> list[ChatMessage]:
        return [openai_message_to_llama_index(message) for message in self.message_dicts()]
