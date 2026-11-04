import json
import uuid
from typing import Annotated, Any, ClassVar, Literal, Self

from fastapi import HTTPException, status
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion_chunk import ChoiceDelta, ChoiceDeltaToolCall, ChoiceDeltaToolCallFunction
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall, Function
from pydantic import BaseModel, Field, ValidationError
from swiss_ai_hub.core.events.agent import ExceptionEvent, HumanInTheLoopRequestEvent, ResponseSchema, StopEvent
from swiss_ai_hub.core.routes import ChatService

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.structured_presentation import StructuredPresentation

type FinishReason = Literal["stop", "tool_calls"]


class OpenaiStructuredRequest(BaseModel):
    """
    The JSON shape an OpenAI caller asked an agent for, and how to hand the result back.

    Both of OpenAI's ways of asking end in the same protocol request, `ResponseSchema`: `response_format`
    (`json_schema` or `json_object`) and a forced call of the one function in `tools`. Only the presentation differs,
    as `content` or as a `tool_calls` entry. Agents do not run caller tools, so any other use of `tools` is refused
    rather than ignored.
    """

    response_schema: Annotated[ResponseSchema, Field(description="The shape, as the agent receives it.")]
    presentation: Annotated[StructuredPresentation, Field(description="Content or a tool call.")]
    param: Annotated[str, Field(description="The request field that asked for it, named in errors.")]

    _NO_PARAMETERS: ClassVar[dict[str, Any]] = {"type": "object", "properties": {}, "additionalProperties": False}

    @classmethod
    def from_request(cls, request: ChatCompletionRequest) -> Self | None:
        """The structured request, None for a plain answer; a 400 for anything an agent cannot honour."""
        if request.functions or request.function_call:
            raise cls._invalid(
                "functions",
                "Agents do not take `functions`. Ask for structured output with `response_format`, or with one tool "
                "in `tools` forced by `tool_choice`.",
            )
        tools = list(request.tools or [])
        if tools and request.tool_choice != "none":
            return cls._forced_function(request, tools)
        if not tools and cls._forces_a_tool(request.tool_choice):
            raise cls._invalid("tool_choice", "`tool_choice` forces a function, but `tools` offers none.")
        return cls._response_format(request.response_format)

    @classmethod
    def _response_format(cls, response_format: dict[str, Any] | None) -> Self | None:
        format_type = (response_format or {}).get("type", "text")
        if format_type == "text":
            return None
        if format_type == "json_object":
            schema = cls._schema("response_format", name="json_object")
        else:
            json_schema = response_format.get("json_schema", {})
            schema = cls._schema(
                "response_format",
                name=json_schema.get("name"),
                description=json_schema.get("description"),
                json_schema=json_schema.get("schema"),
                strict=bool(json_schema.get("strict")),
            )
        return cls(response_schema=schema, presentation=StructuredPresentation.CONTENT, param="response_format")

    @classmethod
    def _forced_function(cls, request: ChatCompletionRequest, tools: list[dict[str, Any]]) -> Self:
        if len(tools) > 1 or tools[0].get("type") != "function":
            raise cls._invalid(
                "tools",
                "Agents do not call caller tools. `tools` may hold exactly one function, forced with `tool_choice`, "
                "whose parameters are the shape of the answer.",
            )
        function = tools[0]["function"]
        if not cls._is_forced(request.tool_choice, function["name"]):
            raise cls._invalid(
                "tool_choice",
                f"Agents do not call caller tools. Force the function with "
                f'`tool_choice: {{"type": "function", "function": {{"name": "{function["name"]}"}}}}` to receive '
                "the answer as its arguments.",
            )
        if (request.response_format or {}).get("type", "text") != "text":
            raise cls._invalid(
                "response_format", "Ask for structured output with `response_format` or a forced tool, not both."
            )
        schema = cls._schema(
            "tools",
            name=function["name"],
            description=function.get("description"),
            json_schema=function["parameters"] if "parameters" in function else cls._NO_PARAMETERS,
            strict=bool(function.get("strict")),
        )
        return cls(response_schema=schema, presentation=StructuredPresentation.TOOL_CALL, param="tool_choice")

    @staticmethod
    def _forces_a_tool(tool_choice: Any) -> bool:
        return tool_choice == "required" or (isinstance(tool_choice, dict) and tool_choice.get("type") == "function")

    @staticmethod
    def _is_forced(tool_choice: Any, function_name: str) -> bool:
        if tool_choice == "required":
            return True
        return (
            isinstance(tool_choice, dict)
            and tool_choice.get("type") == "function"
            and tool_choice.get("function", {}).get("name") == function_name
        )

    @classmethod
    def _schema(cls, param: str, **fields: Any) -> ResponseSchema:
        try:
            return ResponseSchema(**fields)
        except ValidationError as invalid:
            raise cls._invalid(param, f"The requested schema cannot be used: {invalid.errors()[0]['msg']}") from None

    @staticmethod
    def _invalid(param: str, message: str) -> HTTPException:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"message": message, "param": param})

    def unsupported_by(self, model: str) -> HTTPException:
        return self._invalid(self.param, f"Agent '{model}' does not support structured output.")

    def message(self, stop_event: StopEvent | HumanInTheLoopRequestEvent) -> tuple[ChatCompletionMessage, FinishReason]:
        """The answer as OpenAI returns structured output; a turn that ended without the JSON comes back as a refusal,
        never as content the caller would try to parse."""
        structured = getattr(stop_event, "structured_output", None)
        if structured is None:
            return ChatCompletionMessage(role="assistant", content=None, refusal=self._refusal(stop_event)), "stop"
        arguments = json.dumps(structured, ensure_ascii=False)
        if self.presentation == StructuredPresentation.CONTENT:
            return ChatCompletionMessage(role="assistant", content=arguments), "stop"
        call = ChatCompletionMessageFunctionToolCall(
            id=self._call_id(), type="function", function=Function(name=self.response_schema.name, arguments=arguments)
        )
        return ChatCompletionMessage(role="assistant", content=None, tool_calls=[call]), "tool_calls"

    def delta(self, stop_event: StopEvent | HumanInTheLoopRequestEvent) -> tuple[ChoiceDelta, FinishReason]:
        """The same answer as one streamed delta: it is known only once the agent validated it."""
        message, finish_reason = self.message(stop_event)
        tool_calls = [
            ChoiceDeltaToolCall(
                index=index,
                id=call.id,
                type="function",
                function=ChoiceDeltaToolCallFunction(name=call.function.name, arguments=call.function.arguments),
            )
            for index, call in enumerate(message.tool_calls or [])
        ]
        delta = ChoiceDelta(
            role="assistant", content=message.content, refusal=message.refusal, tool_calls=tool_calls or None
        )
        return delta, finish_reason

    @staticmethod
    def _refusal(stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent) -> str:
        if stop_event.is_hitl_request_event:
            return stop_event.question
        text = ChatService.terminal_output_text(getattr(stop_event, "output_messages", None))
        return text or "The agent ended without an answer in the requested format."

    @staticmethod
    def _call_id() -> str:
        return f"call_{uuid.uuid4().hex[:24]}"
