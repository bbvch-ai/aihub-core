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
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    SECTION_START_LINE,
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


def combine_nodes_in_order(
    context_nodes: List[Document],
    locale_handler: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
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
            "namespace": metadata.get(NAMESPACE),
            "type": metadata.get(TYPE),
            "language": metadata.get(LANGUAGE),
            "version": metadata.get(VERSION),
            "created_at": format_unix_timestamp(metadata.get(CREATED_AT)),
            "updated_at": format_unix_timestamp(metadata.get(UPDATED_AT)),
            "inserted_at": format_unix_timestamp(metadata.get(INSERTED_AT)),
        }

        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

        metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())

        doc_header = f"<DOCUMENT {metadata_string}>\n\n"

        text_parts = [doc_header]
        sorted_nodes = sorted(nodes, key=lambda x: x.metadata.get(SECTION_START_LINE, 0))

        for n in sorted_nodes:
            text_parts.append(f"{n.content}\n\n")

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
