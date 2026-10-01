from typing import Annotated

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent


class ToolLoopFinishedEvent(ControlEvent):
    """The answer to `RunToolLoopEvent`: the reply in answering mode, the gathered context in gathering mode."""

    loop: Annotated[
        str, Field(description="The blueprint's tool set this loop runs, telling two loops of one run apart.")
    ] = "tools"
    answer: Annotated[LLMEvent | None, Field(description="The model's final reply, in answering mode.")] = None
    block: Annotated[
        list[ChatMessage], Field(description="The tool results as context for the blueprint's answer, gathering mode.")
    ] = []
    stopped_early: Annotated[bool, Field(description="Whether the loop stopped at its limits.")] = False
