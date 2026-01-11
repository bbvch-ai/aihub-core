"""Utility functions for OpenCode integration."""

import hashlib
from datetime import UTC, datetime
from typing import Any

from aihub_lib.nats.events import (
    ChunkEvent,
    DocumentChangedEvent,
    LLMCostEvent,
    ThoughtEvent,
    ToolErrorEvent,
    ToolOutputEvent,
)


async def get_or_create_opencode_session(
    thread_context: Any,  # ThreadContext (avoid circular import)
    opencode_client: Any,  # AsyncOpencode
    initialization_prompt: str,
) -> str:
    """
    Get existing OpenCode session ID from ThreadContext.

    Creates a new session if this is the first message.

    Args:
        thread_context: ThreadContext instance
        opencode_client: AsyncOpencode client instance
        initialization_prompt: System prompt for new session

    Returns:
        OpenCode session ID
    """
    session_id = await thread_context.get("opencode_session_id")

    if session_id:
        # Existing session - reuse it
        return session_id

    # New session - create it
    session = await opencode_client.session.create()
    session_id = session.id

    # Store in ThreadContext for future messages
    await thread_context.set("opencode_session_id", session_id)

    # Initialize session with system prompt
    await opencode_client.session.init(id=session_id, parts=[{"type": "text", "text": initialization_prompt}])

    return session_id


def convert_opencode_response_to_events(
    response: Any,  # AssistantMessage from OpenCode
    show_file_changes: bool = True,
    show_tool_calls: bool = True,
    verbose_output: bool = False,
) -> list[ChunkEvent | DocumentChangedEvent | ToolOutputEvent | ToolErrorEvent | ThoughtEvent | LLMCostEvent]:
    """
    Convert OpenCode AssistantMessage parts to Swiss AI-Hub protocol events.

    OpenCode response parts are converted to:
    - TextPart → ChunkEvent (AI's textual response)
    - FilePart → DocumentChangedEvent + ChunkEvent (file created/modified)
    - ToolPart (completed) → ToolOutputEvent + ChunkEvent (successful tool execution)
    - ToolPart (error) → ToolErrorEvent + ChunkEvent (failed tool execution)
    - ToolPart (pending/running) → Skipped (no intermediate state tracking)
    - StepStartPart → ThoughtEvent (agent is thinking)
    - StepFinishPart → LLMCostEvent + ThoughtEvent (cost tracking)
    - SnapshotPart → Skipped
    - PatchPart → Skipped

    Args:
        response: AssistantMessage from OpenCode
        show_file_changes: Include file creation/modification events
        show_tool_calls: Include tool execution events
        verbose_output: Include detailed event information (cost display, etc.)

    Returns:
        List of Swiss AI-Hub protocol events
    """
    events: list[ChunkEvent | DocumentChangedEvent | ToolOutputEvent | ToolErrorEvent | ThoughtEvent | LLMCostEvent] = []

    for part in response.parts:
        # 1. TextPart → ChunkEvent
        if part.type == "text":
            events.append(ChunkEvent(content=part.text))

        # 2. FilePart → DocumentChangedEvent + ChunkEvent
        elif part.type == "file" and show_file_changes:
            file_events = format_opencode_file_change(part, verbose_output)
            events.extend(file_events)

        # 3. ToolPart → ToolOutputEvent/ToolErrorEvent + ChunkEvent
        elif part.type == "tool" and show_tool_calls:
            tool_events = format_opencode_tool_call(part, verbose_output)
            events.extend(tool_events)

        # 4. StepStartPart → ThoughtEvent
        elif part.type == "step-start":
            events.append(ThoughtEvent(content="🧠 **Thinking...**\n"))

        # 5. StepFinishPart → LLMCostEvent + ThoughtEvent (verbose)
        elif part.type == "step-finish":
            cost_events = format_opencode_step_finish(part, verbose_output)
            events.extend(cost_events)

        # 6. SnapshotPart, PatchPart → Skip

    return events


def format_opencode_file_change(
    file_part: Any,  # FilePart
    verbose_output: bool = False,
) -> list[ChunkEvent | DocumentChangedEvent]:
    """
    Convert FilePart to DocumentChangedEvent + ChunkEvent.

    Emits both:
    - DocumentChangedEvent for observability/tracing in Phoenix
    - ChunkEvent for user-friendly display in chat

    Args:
        file_part: FilePart from OpenCode response
        verbose_output: Include file preview in ChunkEvent

    Returns:
        List containing DocumentChangedEvent and ChunkEvent
    """
    events: list[ChunkEvent | DocumentChangedEvent] = []

    # Extract file information
    path = file_part.source.path if hasattr(file_part, "source") and file_part.source else "unknown"
    mime_type = getattr(file_part, "mime", None)

    # Extract content if available
    content = None
    content_preview = None
    if hasattr(file_part, "source") and file_part.source and hasattr(file_part.source, "text"):
        text_obj = file_part.source.text
        if hasattr(text_obj, "value"):
            content = text_obj.value
            content_preview = content[:200] if content else None

    # Generate document ID from path (deterministic)
    document_id = hashlib.sha256(path.encode()).hexdigest()[:16]

    # Determine operation (OpenCode doesn't provide explicit state)
    operation = "changed"  # Generic since we can't reliably distinguish create vs modify

    # Get current timestamp
    now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    # 1. Emit DocumentChangedEvent for observability
    events.append(
        DocumentChangedEvent(
            document_id=document_id,
            path=path,
            content=content,
            mime_type=mime_type,
            content_preview=content_preview,
            operation=operation,
            namespace="opencode",  # Mark as OpenCode-generated
        )
    )

    # 2. Emit ChunkEvent for user display
    emoji = "📝"
    chunk_content = f"{emoji} **Changed:** `{path}`\n"

    if verbose_output and content_preview:
        chunk_content += f"```\n{content_preview}...\n```\n"

    events.append(ChunkEvent(content=chunk_content))

    return events


def format_opencode_tool_call(
    tool_part: Any,  # ToolPart
    verbose_output: bool = False,
) -> list[ChunkEvent | ToolOutputEvent | ToolErrorEvent]:
    """
    Convert ToolPart to ToolOutputEvent/ToolErrorEvent + ChunkEvent.

    Only handles completed and error states. Skips pending/running states
    as per user requirement (no intermediate state tracking).

    Emits both:
    - ToolOutputEvent/ToolErrorEvent for observability/tracing in Phoenix
    - ChunkEvent for user-friendly display in chat

    Args:
        tool_part: ToolPart from OpenCode response
        verbose_output: Include tool output/error in ChunkEvent

    Returns:
        List containing semantic event and ChunkEvent, or empty list if pending/running
    """
    events: list[ChunkEvent | ToolOutputEvent | ToolErrorEvent] = []

    tool_name = tool_part.tool if hasattr(tool_part, "tool") else "unknown"
    state = tool_part.state if hasattr(tool_part, "state") else None

    if not state:
        return events

    state_status = state.status if hasattr(state, "status") else None

    # Skip pending/running states (user requirement)
    if state_status in ["pending", "running"]:
        return events

    # Extract common metadata
    title = getattr(state, "title", None)
    input_params = getattr(state, "input", None)
    metadata = getattr(state, "metadata", None)

    # Calculate duration if available
    duration = None
    if hasattr(state, "time") and state.time:
        time_obj = state.time
        if hasattr(time_obj, "start") and hasattr(time_obj, "end"):
            duration = time_obj.end - time_obj.start

    # 1. Handle completed state
    if state_status == "completed":
        output = getattr(state, "output", "")

        # Emit ToolOutputEvent
        events.append(
            ToolOutputEvent(
                name=tool_name,
                title=title,
                output=output,
                input=input_params,
                duration=duration,
                metadata=metadata,
            )
        )

        # Emit ChunkEvent for user display
        chunk_content = f"✅ **Completed:** `{title or tool_name}`\n"
        if verbose_output and output:
            preview = output[:500]
            chunk_content += f"```\n{preview}\n```\n"

        events.append(ChunkEvent(content=chunk_content))

    # 2. Handle error state
    elif state_status == "error":
        error = getattr(state, "error", "Unknown error")

        # Emit ToolErrorEvent
        events.append(
            ToolErrorEvent(
                name=tool_name,
                title=title,
                error=error,
                input=input_params,
                duration=duration,
                metadata=metadata,
            )
        )

        # Emit ChunkEvent for user display
        chunk_content = f"❌ **Failed:** `{title or tool_name}`\n"
        if verbose_output and error:
            preview = error[:500]
            chunk_content += f"```\n{preview}\n```\n"

        events.append(ChunkEvent(content=chunk_content))

    return events


def format_opencode_step_finish(
    step_finish_part: Any,  # StepFinishPart
    verbose_output: bool = False,
) -> list[LLMCostEvent | ThoughtEvent]:
    """
    Convert StepFinishPart to LLMCostEvent + ThoughtEvent (optional).

    Emits:
    - LLMCostEvent for cost tracking/billing (always)
    - ThoughtEvent for user display (only if verbose_output=True)

    Args:
        step_finish_part: StepFinishPart from OpenCode response
        verbose_output: Include cost display in ThoughtEvent

    Returns:
        List containing LLMCostEvent and optionally ThoughtEvent
    """
    events: list[LLMCostEvent | ThoughtEvent] = []

    # Extract cost and token information
    cost = getattr(step_finish_part, "cost", 0.0)
    tokens = getattr(step_finish_part, "tokens", None)

    input_tokens = 0
    output_tokens = 0
    reasoning_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0

    if tokens:
        input_tokens = int(getattr(tokens, "input", 0))
        output_tokens = int(getattr(tokens, "output", 0))
        reasoning_tokens = int(getattr(tokens, "reasoning", 0))

        cache = getattr(tokens, "cache", None)
        if cache:
            cache_read_tokens = int(getattr(cache, "read", 0))
            cache_write_tokens = int(getattr(cache, "write", 0))

    # 1. Emit LLMCostEvent (always)
    # Map OpenCode tokens to Swiss AI-Hub structure
    # OpenCode: input, output, reasoning, cache (read/write)
    # Swiss AI-Hub: prompt_token_count, completion_token_count, embedding_token_count
    prompt_token_count = input_tokens + cache_read_tokens  # Input + cached inputs
    completion_token_count = output_tokens + reasoning_tokens  # Output + reasoning

    # Split cost proportionally between prompt and completion (rough estimate)
    total_tokens = prompt_token_count + completion_token_count
    if total_tokens > 0:
        prompt_tokens_costs = cost * (prompt_token_count / total_tokens)
        completion_tokens_costs = cost * (completion_token_count / total_tokens)
    else:
        prompt_tokens_costs = 0.0
        completion_tokens_costs = 0.0

    events.append(
        LLMCostEvent(
            llm_name="opencode",  # Mark as OpenCode-generated
            prompt_token_count=prompt_token_count,
            completion_token_count=completion_token_count,
            embedding_token_count=0,  # OpenCode doesn't use embeddings
            prompt_tokens_costs=prompt_tokens_costs,
            completion_tokens_costs=completion_tokens_costs,
            embedding_tokens_costs=0.0,
        )
    )

    # 2. Emit ThoughtEvent for user display (verbose only)
    if verbose_output:
        total_tokens = input_tokens + output_tokens + reasoning_tokens
        events.append(ThoughtEvent(content=f"💰 **Cost:** ${cost:.4f} ({total_tokens:,} tokens)\n"))

    return events
