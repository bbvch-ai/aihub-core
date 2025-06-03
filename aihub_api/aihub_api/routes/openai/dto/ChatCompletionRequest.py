from typing import Any, Dict, Iterable, List, Optional, Union

from aihub_lib.records.ReceivedFile import ReceivedFile
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
from typing_extensions import Annotated, Literal


def resolve_message_content(message: Dict[str, Any]) -> Dict[str, Any]:
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

    # Handle ValidatorIterator (check by looking for schema attribute)
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
                # Add other content types as needed
            elif hasattr(part, "dict"):
                # If it's a Pydantic model
                resolved_content.append(part.dict())
            else:
                # Fallback - try to convert to dict somehow
                try:
                    resolved_content.append(dict(part))
                except Exception:
                    pass

        # Create a new message with resolved content
        new_message = message.copy()
        new_message["content"] = resolved_content
        return new_message

    # Content might already be a list of content parts
    return message


def openai_message_to_llama_index(message: Dict[str, Any]) -> ChatMessage:
    """
    Converts an OpenAI message dict to a llama-index ChatMessage.
    Handles both simple string content and complex multimodal content.
    """
    # First, ensure content is properly resolved
    message = resolve_message_content(message)

    role = message.get("role", "user")
    content = message.get("content")
    blocks: List[ContentBlock] = []

    # Process content based on its type
    if isinstance(content, str):
        blocks.append(TextBlock(text=content))
    elif isinstance(content, Iterable) and not isinstance(content, (str, bytes)):
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    blocks.append(TextBlock(text=part.get("text", "")))
                elif part_type == "image_url":
                    image_url = part.get("image_url", {})
                    if isinstance(image_url, dict) and "url" in image_url:
                        blocks.append(ImageBlock(url=image_url.get("url"), detail=image_url.get("detail", "auto")))

    # Create ChatMessage with the processed blocks and additional kwargs
    additional_kwargs = {k: v for k, v in message.items() if k not in ["role", "content"]}

    return ChatMessage(role=MessageRole(role), blocks=blocks, additional_kwargs=additional_kwargs)


class Metadata(BaseModel):
    thread_id: Annotated[
        Optional[str], Field(description="Provide thread ID to continue conversation in an existing thread.")
    ] = None
    display_id: Annotated[Optional[str], Field(description="Gives control over display ID used for this run.")] = None
    reconstruct_history: Annotated[
        Optional[bool],
        Field(
            description="When set to True, message set on UserMessageEvent will be calculated based on thread event history"
        ),
    ] = None
    files: Annotated[
        Optional[List[ReceivedFile]],
        Field(description="List of files to attach to the request, if supported by the model."),
    ] = []


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    messages: Annotated[
        Optional[List[ChatCompletionMessageParam]], Field(description="Messages to complete the chat with.")
    ]
    model: Annotated[Union[str, ChatModel], Field(description="ID of the model to use for the chat completion.")]
    stream: Annotated[bool, Field(description="Enable streaming response.")] = False

    user: Optional[str] = None

    audio: Optional[ChatCompletionAudioParam] = None
    frequency_penalty: Optional[float] = None
    function_call: Optional[completion_create_params.FunctionCall] = None
    functions: Optional[Iterable[completion_create_params.Function]] = None
    logit_bias: Optional[Dict[str, int]] = None
    logprobs: Optional[bool] = None
    max_completion_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    metadata: Optional[Metadata] = None
    modalities: Optional[List[ChatCompletionModality]] = None
    n: Optional[int] = None
    parallel_tool_calls: Optional[bool] = None
    prediction: Optional[ChatCompletionPredictionContentParam] = None
    presence_penalty: Optional[float] = None
    reasoning_effort: Optional[ChatCompletionReasoningEffort] = None
    response_format: Optional[completion_create_params.ResponseFormat] = None
    seed: Optional[int] = None
    service_tier: Optional[Literal["auto", "default"]] = None
    stop: Union[Optional[str], List[str]] = None
    store: Optional[bool] = None
    stream_options: Optional[ChatCompletionStreamOptionsParam] = None
    temperature: Optional[float] = None
    tool_choice: Optional[ChatCompletionToolChoiceOptionParam] = None
    tools: Optional[Iterable[ChatCompletionToolParam]] = None
    top_logprobs: Optional[int] = None
    top_p: Optional[float] = None

    @property
    def llama_index_messages(self):
        """
        Processes a list of OpenAI messages into llama-index ChatMessage objects.
        Handles any message format (dict, model, etc.) and any content format.
        """
        result = []

        for msg in self.messages:
            # Convert message to dict if it's a model
            if hasattr(msg, "model_dump"):
                msg_dict = msg.model_dump(exclude_unset=False)
            elif hasattr(msg, "dict"):
                msg_dict = msg.dict()
            else:
                msg_dict = dict(msg)

            # Convert to llama-index ChatMessage
            result.append(openai_message_to_llama_index(msg_dict))

        return result
