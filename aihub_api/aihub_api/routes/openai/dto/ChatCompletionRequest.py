from typing import Dict, Iterable, List, Optional, Union

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


class ChatCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    chat_id: Annotated[Optional[str], Field(description="ID of the chat to complete.")] = None

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
    metadata: Optional[Dict] = None
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
