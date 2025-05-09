import html
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Optional

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.retriever import Document
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    HEADING_LEVEL,
    INSERTED_AT,
    NODE_TYPE_SUMMARY,
    SECTION_START_LINE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION, )


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


def combine_nodes_in_hierarchical_order(
        context_nodes: List[Document],
        locale_handler: LocaleHandler,
        context_prompt: LocaleString = None,
) -> ChatMessage:
    """
    Combine nodes in hierarchical order, preserving document structure with summaries.
    """
    nodes_per_document = defaultdict(list)

    for context_node in context_nodes:
        if not context_node.metadata or SOURCE not in context_node.metadata:
            raise ValueError(f"Context node must contain metadata {SOURCE}")
        key = context_node.metadata.get(SOURCE)
        nodes_per_document[key].append(context_node)

    documents = []

    for key, nodes in nodes_per_document.items():
        metadata = nodes[0].metadata

        metadata_fields = {
            "source": key,
            "version": metadata.get(VERSION),
            "created_at": format_unix_timestamp(metadata.get(CREATED_AT)),
            "updated_at": format_unix_timestamp(metadata.get(UPDATED_AT)),
            "inserted_at": format_unix_timestamp(metadata.get(INSERTED_AT)),
        }

        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}
        metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())

        doc_header = f"<DOCUMENT {metadata_string}>\n\n"
        text_parts = [doc_header]

        organized_text = organize_document_nodes(nodes)
        text_parts.append(organized_text)

        text_parts.append("</DOCUMENT>\n")
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


def organize_document_nodes(nodes: List[Document]) -> str:
    """
    Organizes document nodes into a hierarchical structure based on heading levels.
    Uses only original heading text from metadata and maintains a logical ordering.
    """
    # Separate summary and content nodes
    summary_nodes = [n for n in nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    content_nodes = [n for n in nodes if n.metadata.get(TYPE) != NODE_TYPE_SUMMARY]

    # Sort summaries by level first, then by position within each level
    sorted_summaries = sorted(
        summary_nodes,
        key=lambda x: (x.metadata.get(HEADING_LEVEL, 0), x.metadata.get(SECTION_START_LINE, 0))
    )

    # Group content by its section position
    content_by_position = defaultdict(list)
    for node in content_nodes:
        pos = node.metadata.get(SECTION_START_LINE, 0)
        content_by_position[pos].append(node)

    # Render the document structure
    result = []

    # Process summaries in order
    for summary in sorted_summaries:
        level = summary.metadata.get(HEADING_LEVEL, 0)

        # Get heading tag based on level (h1, h2, etc.)
        tag = f"h{level}" if 1 <= level <= 6 else "summary"

        # Get heading text from metadata
        heading_text = None
        if 1 <= level <= 6:
            heading_key = f"H{level}"
            if heading_key in summary.metadata:
                heading_text = summary.metadata[heading_key]

        # Add summary with appropriate heading
        if heading_text:
            result.append(f"<{tag}>{heading_text}</{tag}>\n")

        # Always add the summary content
        result.append(f"<summary>{summary.content}</summary>\n\n")

        # Add content associated with this summary's position
        pos = summary.metadata.get(SECTION_START_LINE, 0)
        if pos in content_by_position:
            result.append("<content>\n")
            for content_node in content_by_position[pos]:
                result.append(f"{content_node.content}\n\n")
            result.append("</content>\n\n")
            # Remove processed content
            del content_by_position[pos]

    # Add any remaining content that wasn't associated with summaries
    if content_by_position:
        result.append("<remaining_content>\n")
        for pos in sorted(content_by_position.keys()):
            for content_node in content_by_position[pos]:
                result.append(f"{content_node.content}\n\n")
        result.append("</remaining_content>\n")

    return "".join(result)
