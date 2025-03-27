import json
from typing import Optional

from aihub_lib.displayers.EventDisplayer import EventDisplayer


async def _parse_sse_chunk(line: str) -> Optional[str | dict]:
    """Parse a single Server-Side Event (SSE) line and extract content if available."""
    # Skip empty lines
    if not line.strip() or not line.startswith("data: "):
        return None

    # Remove the "data: " prefix
    data = line[6:]

    # Check for end of stream marker
    if data == "[DONE]":
        return None

    try:
        # Parse the JSON data
        chunk_data = json.loads(data)

        # Check if the response indicates completion
        if chunk_data.get("finish_reason") is not None:
            return chunk_data["usage"]

        # Extract content from the chunk
        if "choices" in chunk_data and chunk_data["choices"]:
            delta = chunk_data["choices"][0].get("delta", {})
            return delta.get("content", "")

    except json.JSONDecodeError:
        pass

    return None


async def _display_streamed_content(
    content: str, buffer: str, max_buffer_length: int, displayer: EventDisplayer, model_name: str
) -> str:
    """Handle buffering and displaying of streamed content."""
    buffer += content

    # Flush buffer at newline boundaries
    while "\n" in buffer:
        section, buffer = buffer.split("\n", 1)
        await displayer.display_chunk(section + "\n", model_name=model_name)

    # If no newline but buffer large, flush to avoid delays
    if len(buffer) > max_buffer_length:
        await displayer.display_chunk(buffer, model_name=model_name)
        buffer = ""

    return buffer
