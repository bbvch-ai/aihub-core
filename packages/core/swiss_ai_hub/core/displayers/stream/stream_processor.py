from typing import TYPE_CHECKING

from swiss_ai_hub.core.displayers.buffer.stream_buffer import StreamBuffer
from swiss_ai_hub.core.displayers.parser.tag_parser import TagParser
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

    async def process_chunk(self, chunk_content: str) -> None:
        """Process a single chunk of streamed content."""
        self.aggregate += chunk_content
        for content_type, char in self.parser.process_content(chunk_content):
            await self._handle_character(content_type, char)

    async def finalize(self) -> str:
        """Flush remaining content and return aggregate."""
        for content_type, char in self.parser.flush_remaining():
            await self._handle_character(content_type, char)

        await self._flush_buffers()
        return self.aggregate

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
