import html
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION,
)

_headers_in_order = [H6, H5, H4, H3, H2, H1]


def sanitize_metadata_value(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    sanitized_value = value.replace("'", "").strip()
    sanitized_value = html.escape(sanitized_value)
    return sanitized_value


def format_unix_timestamp(timestamp: Optional[int]) -> Optional[str]:
    if timestamp is None or timestamp <= 0:
        return None
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%d.%m.%Y")
    except (ValueError, OverflowError):
        return None


def remove_markdown_images(content: str) -> str:
    """
    Remove markdown image syntax from content.
    Matches patterns like: ![description](url)
    """
    # [^\]]{10,1000} matches non bracket characters between 10 and 1000 times, [^\s\)]{10,2048} matches non whitespace and non closing parenthesis characters between 10 and 2048 times
    markdown_image_pattern = r"^!\[[^\]]{10,1000}\]\(https?:\/\/[^\s\)]{10,2048}\)$"
    cleaned_content = re.sub(markdown_image_pattern, "", content)

    cleaned_content = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_content)
    cleaned_content = cleaned_content.strip()

    return cleaned_content


def is_image_only_node(content: str) -> bool:
    cleaned_content = remove_markdown_images(content)

    return not cleaned_content.strip()


def combine_nodes_in_order(
    context_nodes: List[IngestedNode],
    locale_handler: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document: Dict[str, List[IngestedNode]] = defaultdict(list)

    for context_node in context_nodes:
        key = context_node.source
        nodes_per_document[key].append(context_node)

    documents = []

    for key, nodes in nodes_per_document.items():
        node: IngestedNode = nodes[0]

        metadata_fields = {
            SOURCE: key,
            NAMESPACE: node.namespace,
            TYPE: node.content_type,
            LANGUAGE: node.language,
            VERSION: node.version,
            CREATED_AT: node.created_at,
            UPDATED_AT: node.updated_at,
            INSERTED_AT: node.inserted_at,
        }

        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

        metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())

        doc_header = f"<REFERENCE_DOCUMENT {metadata_string}>\n\n"

        text_parts = [doc_header]
        sorted_nodes = sorted(nodes, key=lambda x: x.section_start_line or 1)

        for n in sorted_nodes:
            if is_image_only_node(n.content):
                text_parts.append("<IMAGE>\n\n")
            else:
                text_parts.append(f"{n.content}\n\n")

        text_parts.append("</REFERENCE_DOCUMENT>\n")
        text_parts.append("\n---\n")

        documents.append("".join(text_parts))

    if context_prompt:
        context_prompt_locale = LocaleHandler(locale_handler.locale).extract(context_prompt, locale_handler.locale)
    else:
        context_prompt_locale = locale_handler("lib.prompt.rag.context_prompt")

    return ChatMessage(
        role=MessageRole.SYSTEM,
        content=context_prompt_locale.format(context_str="".join(documents)),
    )
