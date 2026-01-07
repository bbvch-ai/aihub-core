"""Utility functions for NamespaceSelectionAgent."""

import logging

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString

logger = logging.getLogger(__name__)


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
            logger.error(f"Invalid bucket '{bucket_name}' in LLM selection")
            return False
        if namespace_name not in available_namespaces[bucket_name]:
            logger.error(f"Invalid namespace '{namespace_name}' for bucket '{bucket_name}'")
            return False
    return True
