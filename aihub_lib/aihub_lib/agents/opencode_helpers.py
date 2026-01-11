"""
Helper functions for OpenCode SDK integration.

This module provides properly typed utilities for converting between
LlamaIndex ChatMessage blocks and OpenCode Part types, processing
OpenCode events, and managing session state.
"""

from typing import Annotated

from llama_index.core.base.llms.types import (
    AudioBlock,
    ChatMessage,
    DocumentBlock,
    ImageBlock,
    TextBlock,
    VideoBlock,
)
from opencode_ai import AsyncOpencode
from opencode_ai.types import (
    FilePart,
    Part,
    StepFinishPart,
    StepStartPart,
    TextPartInputParam,
    ToolPart,
    ToolStateCompleted,
    ToolStateError,
)

from aihub_lib.agents.context.ThreadContext import ThreadContext
from aihub_lib.nats.events import (
    DocumentChangedEvent,
    LLMCostEvent,
    ThoughtEvent,
    ToolErrorEvent,
    ToolOutputEvent,
)


def chatmessage_to_opencode_parts(
    message: Annotated[ChatMessage, "LlamaIndex ChatMessage with multimodal blocks"],
) -> Annotated[list[Part], "OpenCode-compatible Part list for session.chat()"]:
    """
    Convert ChatMessage blocks to OpenCode Part types.

    Handles multimodal content including text, images, documents, audio, and video.
    OpenCode currently supports text and file parts.
    """
    parts: list[Part] = []

    # Extract blocks from message
    blocks = message.blocks if hasattr(message, "blocks") and message.blocks else []

    # If no blocks, fall back to content string
    if not blocks and message.content:
        parts.append(TextPartInputParam(type="text", text=message.content))
        return parts

    # Process each block
    for block in blocks:
        if isinstance(block, TextBlock):
            parts.append(TextPartInputParam(type="text", text=block.text))

        elif isinstance(block, (ImageBlock, DocumentBlock, AudioBlock, VideoBlock)):
            # Extract file information from block
            if isinstance(block, ImageBlock):
                url = block.url or ""
                mime = "image/png"  # Default, would be better to detect from URL
                filename = block.filename or "image.png"
            elif isinstance(block, DocumentBlock):
                url = block.url or ""
                mime = "application/pdf"  # Default
                filename = block.filename or "document.pdf"
            elif isinstance(block, AudioBlock):
                url = block.url or ""
                mime = "audio/mpeg"  # Default
                filename = block.filename or "audio.mp3"
            elif isinstance(block, VideoBlock):
                url = block.url or ""
                mime = "video/mp4"  # Default
                filename = block.filename or "video.mp4"
            else:
                continue

            # OpenCode FilePartInputParam requires url and mime
            if url:
                from opencode_ai.types import FilePartInputParam

                parts.append(
                    FilePartInputParam(
                        type="file",
                        url=url,
                        mime=mime,
                        filename=filename,
                    )
                )

    # Ensure at least one text part if no parts were created
    if not parts:
        parts.append(TextPartInputParam(type="text", text=message.content or ""))

    return parts


def filepart_to_document_changed_event(
    file_part: Annotated[FilePart, "OpenCode FilePart from event stream"],
) -> Annotated[DocumentChangedEvent, "Swiss AI-Hub document change event"]:
    """
    Convert OpenCode FilePart to DocumentChangedEvent.

    FilePart represents file operations (create, modify) performed by the AI agent.
    """
    # Extract file content if available
    content = None
    if file_part.source:
        if hasattr(file_part.source, "text"):
            content = file_part.source.text

    # Create content preview (first 200 chars)
    content_preview = None
    if content:
        content_preview = content[:200] + ("..." if len(content) > 200 else "")

    # Determine operation from context
    # OpenCode doesn't explicitly mark create vs modify, so we use "changed"
    operation = "changed"

    return DocumentChangedEvent(
        document_id=file_part.id,
        path=file_part.url,
        content=content,
        mime_type=file_part.mime,
        content_preview=content_preview,
        operation=operation,
        namespace=file_part.session_id,
        metadata={
            "message_id": file_part.message_id,
            "filename": file_part.filename,
        },
    )


def toolpart_to_tool_events(
    tool_part: Annotated[ToolPart, "OpenCode ToolPart from event stream"],
) -> Annotated[
    ToolOutputEvent | ToolErrorEvent | None,
    "Swiss AI-Hub tool event (only for completed/error states)",
]:
    """
    Convert OpenCode ToolPart to ToolOutputEvent or ToolErrorEvent.

    Only processes completed and error states. Pending and running states are skipped
    to avoid cluttering the event stream.
    """
    state = tool_part.state

    # Skip intermediate states (pending, running)
    if state.status in ("pending", "running"):
        return None

    # Extract common fields
    tool_name = tool_part.tool
    tool_title = None
    tool_input = None
    duration = None
    metadata = {
        "call_id": tool_part.call_id,
        "message_id": tool_part.message_id,
        "session_id": tool_part.session_id,
    }

    if isinstance(state, ToolStateCompleted):
        # Success case
        tool_title = state.title
        tool_input = state.input
        duration = state.time.duration if hasattr(state.time, "duration") else None

        return ToolOutputEvent(
            name=tool_name,
            title=tool_title,
            output=state.output,
            input=tool_input,
            duration=duration,
            metadata={**metadata, **state.metadata} if state.metadata else metadata,
        )

    elif isinstance(state, ToolStateError):
        # Error case
        tool_input = state.input
        duration = state.time.duration if hasattr(state.time, "duration") else None

        return ToolErrorEvent(
            name=tool_name,
            title=tool_title,
            error=state.error,
            input=tool_input,
            duration=duration,
            metadata=metadata,
        )

    return None


def step_start_to_thought_event(
    step_start: Annotated[StepStartPart, "OpenCode StepStartPart from event stream"],
) -> Annotated[ThoughtEvent, "Swiss AI-Hub thought event marking agent reasoning start"]:
    """
    Convert OpenCode StepStartPart to ThoughtEvent.

    Marks the beginning of an agent reasoning step.
    """
    return ThoughtEvent(
        thought="Agent started reasoning step",
        metadata={
            "step_id": step_start.id,
            "message_id": step_start.message_id,
            "session_id": step_start.session_id,
        },
    )


def step_finish_to_cost_event(
    step_finish: Annotated[StepFinishPart, "OpenCode StepFinishPart from event stream"],
) -> Annotated[LLMCostEvent, "Swiss AI-Hub cost tracking event"]:
    """
    Convert OpenCode StepFinishPart to LLMCostEvent.

    Maps OpenCode token structure to Swiss AI-Hub cost tracking:
    - input + cache.read → prompt_token_count
    - output + reasoning → completion_token_count
    - Cost is split proportionally between prompt and completion tokens
    """
    tokens = step_finish.tokens

    # Calculate token counts
    prompt_tokens = int(tokens.input + tokens.cache.read)
    completion_tokens = int(tokens.output + tokens.reasoning)
    total_tokens = prompt_tokens + completion_tokens

    # Split cost proportionally
    prompt_tokens_costs = 0.0
    completion_tokens_costs = 0.0
    if total_tokens > 0:
        prompt_ratio = prompt_tokens / total_tokens
        completion_ratio = completion_tokens / total_tokens
        prompt_tokens_costs = step_finish.cost * prompt_ratio
        completion_tokens_costs = step_finish.cost * completion_ratio

    return LLMCostEvent(
        llm_name="opencode",
        prompt_token_count=prompt_tokens,
        completion_token_count=completion_tokens,
        embedding_token_count=0,  # OpenCode doesn't track embeddings separately
        prompt_tokens_costs=prompt_tokens_costs,
        completion_tokens_costs=completion_tokens_costs,
        embedding_tokens_costs=0.0,
    )


async def get_or_create_opencode_session(
    thread_context: Annotated[ThreadContext, "Persistent thread-level state storage"],
    opencode_client: Annotated[AsyncOpencode, "OpenCode async client instance"],
) -> Annotated[str, "OpenCode session ID for the current thread"]:
    """
    Get existing OpenCode session ID from ThreadContext or create new session.

    The session ID is stored in ThreadContext under the key "opencode_session_id"
    to maintain continuity across conversation turns. New sessions are created
    on first message in a thread.

    NOTE: System prompt/initialization should be configured in the OpenCode server's
    AGENTS.md file, not passed here.
    """
    session_id = await thread_context.get("opencode_session_id")

    if not session_id:
        # Create new session (no system prompt - configured in OpenCode server)
        session = await opencode_client.session.init()
        session_id = session.id
        await thread_context.set("opencode_session_id", session_id)

    return session_id
