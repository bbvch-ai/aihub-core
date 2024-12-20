from pydantic import Field

from aihub_lib.nats.events.display.DisplayEvent import DisplayEvent


class ChunkEvent(DisplayEvent):
    """
    An event representing a portion of output or generated content (a "chunk") that is
    streamed or delivered in segments—common in incremental output scenarios like LLM
    token streaming.

    ### Why ChunkEvent?
    In conversational or streaming AI outputs, the model might emit content in pieces rather
    than all at once. `ChunkEvent` allows the frontend or other consumers to display partial
    responses as they are generated, improving user experience by not forcing them to wait
    for the entire answer.
    """

    model_name: str = Field(..., description="The name of the AI model generating the chunks.")
    content: str = Field(..., description="The actual chunk of text or data produced at this stage.")
