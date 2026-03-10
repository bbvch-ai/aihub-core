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
from swiss_ai_hub.core.nats.events.user.UserUploadedFile import UserUploadedFile


def resolve_message_content(message: dict[str, Any]) -> dict[str, Any]:
    """
    Resolves the content field in a message, handling ValidatorIterator instances.
    Returns a new message dict with properly resolved content.
    """
    if "content" not in message:
        return message

    content = message["content"]

    # If content is already a string, no processing needed
    if isinstance(content, str):
        return message

    if hasattr(content, "schema"):
        resolved_content = []
        # Iterate through the validator iterator to extract content parts
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    resolved_content.append({"type": "text", "text": part.get("text", "")})
                elif part_type == "image_url":
                    resolved_content.append({"type": "image_url", "image_url": part.get("image_url", {})})
            elif hasattr(part, "dict"):
                # If it's a Pydantic model
                resolved_content.append(part.dict())
            else:
                # Fallback - try to convert to dict somehow
                try:
                    resolved_content.append(dict(part))
                except Exception:
                    pass

        new_message = message.copy()
        new_message["content"] = resolved_content
        return new_message

    # Content might already be a list of content parts
    return message


def openai_message_to_llama_index(message: dict[str, Any]) -> ChatMessage:
    """
    Converts an OpenAI message dict to a llama-index ChatMessage.
    Handles both simple string content and complex multimodal content.
    """
    # First, ensure content is properly resolved
    message = resolve_message_content(message)

    role = message.get("role", "user")
    content = message.get("content")
    blocks: list[ContentBlock] = []

    if isinstance(content, str):
        blocks.append(TextBlock(text=content))
    elif isinstance(content, Iterable) and not isinstance(content, str | bytes):
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    blocks.append(TextBlock(text=part.get("text", "")))
                elif part_type == "image_url":
                    image_url = part.get("image_url", {})
                    if isinstance(image_url, dict) and "url" in image_url:
                        blocks.append(ImageBlock(url=image_url.get("url"), detail=image_url.get("detail", "auto")))

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
