from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent
from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent


class MetaAnswerReadyEvent(ControlEvent):
    """
    Internal hand-off: the self-awareness answer has finished streaming its chunks, and a separate
    step should now emit the terminal stop event.

    Splitting "stream the answer" from "stop the run" into two steps means the terminal stop event is
    published a full dispatch cycle after the last chunk — mirroring the normal pipeline (respond →
    stop) instead of emitting both back-to-back from one step. That back-to-back emission let the stop
    event race its own chunks in the streaming layer and blank the answer in the chat UI.

    Control-only (not displayed): the chunks already carried the visible content. Carries the streamed
    `LLMStopEvent` so the stop step can re-emit it verbatim as the run's terminal event.
    """

    stop_event: Annotated[LLMStopEvent, Field(description="The streamed answer's stop event, re-emitted to terminate.")]
