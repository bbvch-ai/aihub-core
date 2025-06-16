import html
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock
from llama_index.core.prompts import RichPromptTemplate

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessService import AnonymousFileAccessService
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
    NODE_CONTENT_TYPE_FIGURE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION,
    NODE_CONTENT_TYPE,
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
    context_nodes: List[IngestedNode],
    t: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document: Dict[str, List[IngestedNode]] = defaultdict(list)

    for context_node in context_nodes:
        key = context_node.source
        nodes_per_document[key].append(context_node)

    context_blocks: List[ImageBlock | TextBlock] = []
    for key, nodes in nodes_per_document.items():
        node: IngestedNode = nodes[0]

        metadata_fields = {
            SOURCE: key,
            NAMESPACE: node.namespace,
            TYPE: node.type,
            NODE_CONTENT_TYPE: node.content_type,
            LANGUAGE: node.language,
            VERSION: node.version,
            CREATED_AT: node.created_at,
            UPDATED_AT: node.updated_at,
            INSERTED_AT: node.inserted_at,
        }

        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

        metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())

        doc_header = f"<REFERENCE_DOCUMENT {metadata_string}>\n\n"

        context_blocks.append(TextBlock(text=doc_header))
        sorted_nodes = sorted(nodes, key=lambda x: x.section_start_line or 1)

        for n in sorted_nodes:
            content = n.content

            if n.content_type == NODE_CONTENT_TYPE_FIGURE:
                image_path = content.split("](")[-1][:-1]
                container, blob_path = image_path.split("/", 1)
                image_url = AnonymousFileAccessService.generate_sas_url(container, blob_path, lifetime_hours=1)
                context_blocks.append(ImageBlock(url=image_url))
            else:
                context_blocks.append(TextBlock(text=(f"{content}\n\n")))

        context_blocks.append(TextBlock(text="</REFERENCE_DOCUMENT>\n\n---\n"))

    if context_prompt:
        context_prompt_locale = t.extract(context_prompt, t.locale)
    else:
        context_prompt_locale = t("lib.prompt.rag.context_prompt")

    messages = RichPromptTemplate(
        template_str=context_prompt_locale,
    ).format_messages(context_blocks=context_blocks)

    return messages[0]
