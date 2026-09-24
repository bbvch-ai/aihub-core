from typing import TYPE_CHECKING

from swiss_ai_hub.core.displayers.buffer.stream_buffer import StreamBuffer
from swiss_ai_hub.core.displayers.parser.tag_parser import TagParser
from swiss_ai_hub.core.displayers.parser.tool_call_markup import ToolCallMarkup
from swiss_ai_hub.core.displayers.stream.content_type import ContentType

if TYPE_CHECKING:
    from swiss_ai_hub.core.displayers.event_displayer import EventDisplayer


class StreamProcessor:
    """Internal processor for handling LLM stream output."""

    def __init__(self, displayer: "EventDisplayer", model_name: str):
        self.displayer = displayer
        self.model_name = model_name
        self.parser = TagParser()
        self.regular_buffer = StreamBuffer()
        self.thinking_buffer = StreamBuffer()
        self.aggregate = ""
        self.withheld = ""
        self.deciding = True
        self.suppressing = False

    async def process_chunk(self, chunk_content: str) -> None:
        """Process a single chunk of streamed content."""
        self.aggregate += chunk_content
        released = self._release(chunk_content)
        if released is None:
            return

        for content_type, char in self.parser.process_content(released):
            await self._handle_character(content_type, char)

    async def finalize(self) -> str:
        """Flush remaining content and return the aggregate the user was actually shown."""
        if self.suppressing:
            await self.displayer.display_thought(self.aggregate)
            return ""

        for content_type, char in self.parser.process_content(self._release_withheld()):
            await self._handle_character(content_type, char)

        for content_type, char in self.parser.flush_remaining():
            await self._handle_character(content_type, char)

        await self._flush_buffers()
        return ToolCallMarkup.strip(self.aggregate)

    def _release(self, chunk_content: str) -> str | None:
        """Withhold the opening of a stream until a whole-message ReAct object is ruled in or out.

        A ReAct object carries no opening delimiter to switch on, so the decision needs the first
        few characters — bounded by the length of ``{"action":``. Anything else starts flowing
        immediately; a match never reaches the answer at all.
        """
        if self.suppressing:
            return None
        if not self.deciding:
            return chunk_content

        self.withheld += chunk_content
        if ToolCallMarkup.opens_react_object(self.withheld):
            self.suppressing = True
            return None
        if ToolCallMarkup.may_open_react_object(self.withheld):
            return None

        return self._release_withheld()

    def _release_withheld(self) -> str:
        """Hand back whatever the gate was holding — a stream can also end while still undecided."""
        self.deciding = False
        released, self.withheld = self.withheld, ""
        return released

    async def _handle_character(self, content_type: ContentType, char: str) -> None:
        """Handle a single character based on its type."""
        if not char:  # Empty string signals state change
            if content_type == ContentType.THINKING:
                await self._flush_regular()
            else:
                await self._flush_thinking()
            return

        if content_type == ContentType.THINKING:
            if self.thinking_buffer.add(char):
                await self._flush_thinking()
        else:
            if self.regular_buffer.add(char):
                await self._flush_regular()

    async def _flush_regular(self) -> None:
        """Flush regular content buffer."""
        if self.regular_buffer:
            content = self.regular_buffer.get_and_clear()
            await self.displayer.display_chunk(content, self.model_name)

    async def _flush_thinking(self) -> None:
        """Flush thinking content buffer."""
        if self.thinking_buffer:
            content = self.thinking_buffer.get_and_clear()
            await self.displayer.display_thought(content)

    async def _flush_buffers(self) -> None:
        """Flush all buffers."""
        await self._flush_thinking()
        await self._flush_regular()
