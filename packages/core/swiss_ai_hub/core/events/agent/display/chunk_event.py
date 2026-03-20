from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ChunkEvent(DisplayEvent):
    """
    An event representing a portion of output or generated content (a "chunk") that is
    streamed or delivered in segments - common in incremental output scenarios like LLM
    token streaming.

    ### Why ChunkEvent?
    In conversational or streaming AI outputs, the model might emit content in pieces rather
    than all at once. `ChunkEvent` allows the frontend or other consumers to display partial
    responses as they are generated, improving user experience by not forcing them to wait
    for the entire answer.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.chunk_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.chunk_event.description")

    content: Annotated[str, Field(description="The actual chunk of text or data produced at this stage.")] = ""
    model_name: Annotated[str, Field(description="The name of the AI model generating the chunks.")] = "aihub"
