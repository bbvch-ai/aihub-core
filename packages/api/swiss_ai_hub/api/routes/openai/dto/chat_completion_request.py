from collections.abc import Iterable
from typing import Annotated, Any, Literal

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
from pydantic import BaseModel, ConfigDict, Field
from swiss_ai_hub.core.events.agent import UserUploadedFile


def _resolve_dict_part(part: dict[str, Any]) -> dict[str, Any] | None:
    part_type = part.get("type")
    if part_type == "text":
        return {"type": "text", "text": part.get("text", "")}
    if part_type == "image_url":
        return {"type": "image_url", "image_url": part.get("image_url", {})}
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

    if isinstance(content, str):
        return message

    if not hasattr(content, "schema"):
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
    service_tier: Literal["auto", "default"] | None = None
    stop: str | None | list[str] = None
    store: bool | None = None
    stream_options: ChatCompletionStreamOptionsParam | None = None
    temperature: float | None = None
    tool_choice: ChatCompletionToolChoiceOptionParam | None = None
    tools: Iterable[ChatCompletionToolParam] | None = None
    top_logprobs: int | None = None
    top_p: float | None = None

    @property
    def llama_index_messages(self):
        """
        Processes a list of OpenAI messages into llama-index ChatMessage objects.
        Handles any message format (dict, model, etc.) and any content format.
        """
        result = []

        for msg in self.messages:
            if hasattr(msg, "model_dump"):
                msg_dict = msg.model_dump(exclude_unset=False)
            elif hasattr(msg, "dict"):
                msg_dict = msg.dict()
            else:
                msg_dict = dict(msg)

            result.append(openai_message_to_llama_index(msg_dict))

        return result
