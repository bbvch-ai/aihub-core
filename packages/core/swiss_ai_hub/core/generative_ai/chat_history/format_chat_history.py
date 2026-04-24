from llama_index.core.base.llms.types import ChatMessage


def _condense(content: str) -> str:
    lines = [line.strip() for line in content.splitlines()]
    return "\n".join(line for line in lines if line)


def format_chat_history(chat_history: list[ChatMessage]) -> str:
    """Serialize chat messages as ``role: content`` entries for inclusion in prompt templates.

    Within each message the content keeps its line structure, but blank lines and
    per-line indentation are stripped — memory-origin system messages ship with a
    heavily-formatted Jinja template (blank separators between sections, indented
    bullet blocks) that inflates the guard prompt without carrying information.
    Empty messages (e.g. tool-call placeholders) are skipped.

    Caveat: because indentation is stripped unconditionally, any content that relies
    on it (code blocks, markdown lists, quoted text) will flatten. This is fine for
    the guard-sufficiency use case but may be unsuitable for callers needing fidelity.
    """
    entries = []
    for message in chat_history:
        if not message.content:
            continue
        condensed = _condense(message.content)
        if not condensed:
            continue
        entries.append(f"{message.role.value}:\n{condensed}")
    return "\n".join(entries)
