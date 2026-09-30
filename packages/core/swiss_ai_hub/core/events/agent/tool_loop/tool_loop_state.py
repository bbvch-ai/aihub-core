from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.semantic.llm.message import Message
from swiss_ai_hub.core.events.agent.tool_loop.tool_definition import ToolDefinition
from swiss_ai_hub.core.events.agent.tool_loop.tool_loop_mode import ToolLoopMode


class ToolLoopState(BaseModel):
    """Everything the loop knows between two of its steps, carried on its events rather than kept elsewhere.

    Steps of one run may execute on different runners, so the loop's conversation, the tools it offers and what it
    gathered travel with the iteration; the trace then shows the loop's full state at every step.
    """

    messages: Annotated[list[Message], Field(description="The loop's conversation so far, tool calls and results.")]
    tools: Annotated[list[ToolDefinition], Field(description="The tools offered to the model in this run.")] = []
    mode: Annotated[ToolLoopMode, Field(description="Whether the loop answers or gathers context.")]
    iteration: Annotated[int, Field(description="How many decisions the model has made so far.", ge=0)] = 0
    tool_calls_made: Annotated[int, Field(description="How many tool calls ran so far.", ge=0)] = 0
    max_iterations: Annotated[int | None, Field(description="The call's own iteration limit, if any.")] = None
    cite_sources: Annotated[bool, Field(description="Whether tools tell the model to cite what they return.")] = True
    gathered: Annotated[
        list[ChatMessage], Field(description="The tool results as context, for the blueprint's own answer.")
    ] = []
