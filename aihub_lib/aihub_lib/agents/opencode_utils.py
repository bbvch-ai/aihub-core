"""Utility functions for OpenCode integration."""

from typing import Any

from aihub_lib.nats.events import ChunkEvent


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
) -> list[ChunkEvent]:
    """
    Convert OpenCode AssistantMessage parts to ChunkEvents.

    OpenCode response parts can be:
    - TextPart: AI's textual response
    - FilePart: File created/modified
    - ToolPart: Tool execution (e.g., running tests)
    - SnapshotPart: Code snapshot

    Args:
        response: AssistantMessage from OpenCode
        show_file_changes: Include file creation/modification events
        show_tool_calls: Include tool execution events
        verbose_output: Include detailed event information

    Returns:
        List of ChunkEvents to send to user
    """
    events: list[ChunkEvent] = []

    for part in response.parts:
        if part.type == "text":
            # AI's textual response
            events.append(ChunkEvent(content=part.text))

        elif part.type == "file" and show_file_changes:
            # File was created or modified
            file_event = format_opencode_file_change(part, verbose_output)
            if file_event:
                events.append(file_event)

        elif part.type == "tool" and show_tool_calls:
            # Tool was executed (e.g., pytest, make pr-ready)
            tool_event = format_opencode_tool_call(part, verbose_output)
            if tool_event:
                events.append(tool_event)

        elif part.type == "snapshot":
            # Code snapshot (usually not shown to user)
            if verbose_output:
                events.append(ChunkEvent(content=f"📸 **Snapshot:** {part.name}\n"))

    return events


def format_opencode_file_change(
    file_part: Any,  # FilePart
    verbose_output: bool = False,
) -> ChunkEvent | None:
    """
    Format file creation/modification as user-friendly message.

    Args:
        file_part: FilePart from OpenCode response
        verbose_output: Include file preview if available

    Returns:
        ChunkEvent with formatted message, or None if error
    """
    path = file_part.source.path if hasattr(file_part, "source") else "unknown"

    # Determine if created or modified
    action = "📝 Modified" if getattr(file_part, "modified", False) else "✅ Created"

    content = f"{action}: `{path}`\n"

    # Show file preview if available
    if verbose_output and hasattr(file_part, "source") and hasattr(file_part.source, "text"):
        preview = file_part.source.text[:200]
        content += f"```python\n{preview}...\n```\n"

    return ChunkEvent(content=content)


def format_opencode_tool_call(
    tool_part: Any,  # ToolPart
    verbose_output: bool = False,
) -> ChunkEvent | None:
    """
    Format tool execution as user-friendly message.

    Args:
        tool_part: ToolPart from OpenCode response
        verbose_output: Include tool output if available

    Returns:
        ChunkEvent with formatted message, or None if error
    """
    tool_name = tool_part.name if hasattr(tool_part, "name") else "unknown"
    state = tool_part.state if hasattr(tool_part, "state") else None

    # Determine emoji based on state
    if state == "completed":
        emoji = "✅"
        status = "Completed"
    elif state == "error":
        emoji = "❌"
        status = "Failed"
    elif state == "running":
        emoji = "⏳"
        status = "Running"
    else:
        emoji = "🔧"
        status = "Executing"

    content = f"{emoji} **{status}:** `{tool_name}`\n"

    # Show output if available and verbose
    if verbose_output and hasattr(tool_part, "output"):
        output = tool_part.output[:500]  # Limit to 500 chars
        content += f"```\n{output}\n```\n"

    return ChunkEvent(content=content)
