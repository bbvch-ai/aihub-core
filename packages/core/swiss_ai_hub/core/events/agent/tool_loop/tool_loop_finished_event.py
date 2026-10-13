from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_event import LLMEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolLoopFinishedEvent(ControlAndDisplayEvent):
    """The answer to `RunToolLoopEvent`: the reply in answering mode, the gathered context in gathering mode."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_loop_finished_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_loop_finished_event.description"
    )

    loop: Annotated[
        str, Field(description="The blueprint's tool set this loop runs, telling two loops of one run apart.")
    ] = "tools"
    answer: Annotated[LLMEvent | None, Field(description="The model's final reply, in answering mode.")] = None
    block: Annotated[
        list[ChatMessage], Field(description="The tool results as context for the blueprint's answer, gathering mode.")
    ] = []
    stopped_early: Annotated[bool, Field(description="Whether the loop stopped at its limits.")] = False
