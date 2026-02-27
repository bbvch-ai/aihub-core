"""Download user-uploaded files and format them as LLM context."""

from aihub_lib.infrastructure.s3.use_s3 import download_user_file
from aihub_lib.nats.topics import AgentInstanceTopic


def download_and_format_files(
    files: list,
    topic: AgentInstanceTopic,
) -> str:
    """Download all attached files and format them as context for the LLM."""
    parts: list[str] = []
    for uploaded in files:
        raw_bytes = download_user_file(topic.agent_class, topic.agent_id, uploaded)
        text = raw_bytes.decode("utf-8", errors="replace")
        parts.append(f"--- {uploaded.filename} ({len(raw_bytes)} bytes) ---\n{text}")
    return "\n\n".join(parts)
