import logging

from swiss_ai_hub.core.i18n.LocaleHandler import LocaleHandler
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

logger = logging.getLogger(__name__)


def truncate_conversation_history(history: list[dict[str, str]], max_entries: int) -> list[dict[str, str]]:
    """Truncate conversation history, keeping first entry (original query) and most recent entries."""
    if len(history) <= max_entries:
        return history
    return [history[0]] + history[-(max_entries - 1) :]


def format_available_namespaces(available_namespaces: dict[str, list[str]]) -> str:
    """Format available namespaces for LLM prompt."""
    lines = []
    for bucket_name, namespaces in available_namespaces.items():
        lines.append(f"Bucket '{bucket_name}':")
        for ns in namespaces:
            lines.append(f"  - {ns}")
    return "\n".join(lines)


def format_conversation_history(conversation_history: list[dict[str, str]]) -> str:
    """Format conversation history for LLM prompt."""
    lines = []
    for entry in conversation_history:
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def format_approval_question(
    selected: dict[str, str],
    template: LocaleString,
    t: LocaleHandler,
) -> str:
    """Format the approval question with selected namespaces."""
    namespace_lines = []
    for bucket, namespace in selected.items():
        namespace_lines.append(f"- **{bucket}**: {namespace}")
    namespaces_str = "\n".join(namespace_lines)

    return t.extract(template).format(namespaces=namespaces_str)


def validate_namespace_selection(
    selected: dict[str, str],
    available_namespaces: dict[str, list[str]],
) -> bool:
    """Validate that LLM selection references valid buckets and namespaces."""
    for bucket_name, namespace_name in selected.items():
        if bucket_name not in available_namespaces:
            logger.error(
                "LLM hallucination detected - invalid bucket '%s' (attempted: %s, available: %s)",
                bucket_name,
                selected,
                list(available_namespaces.keys()),
            )
            return False
        if namespace_name not in available_namespaces[bucket_name]:
            logger.error(
                "LLM hallucination detected - invalid namespace '%s' for bucket '%s' (attempted: %s, available: %s)",
                namespace_name,
                bucket_name,
                selected,
                available_namespaces[bucket_name],
            )
            return False
    return True
