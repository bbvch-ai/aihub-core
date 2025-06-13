import html
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessService import AnonymousFileAccessService
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.utils.insert_images_into_messages import MARKDOWN_IMAGE_PATTERN
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


def combine_nodes_in_order(
    context_nodes: List[IngestedNode],
    locale_handler: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document: Dict[str, List[IngestedNode]] = defaultdict(list)

    for context_node in context_nodes:
        key = context_node.source
        nodes_per_document[key].append(context_node)

    if context_prompt:
        context_prompt_locale = LocaleHandler(locale_handler.locale).extract(context_prompt, locale_handler.locale)
    else:
        context_prompt_locale = locale_handler("lib.prompt.rag.context_prompt")

    prompt_parts = context_prompt_locale.split("{context_str}")

    blocks = []

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

        text_blocks = [TextBlock(text=prompt_parts[0]), TextBlock(text=doc_header)]
        sorted_nodes = sorted(nodes, key=lambda x: x.section_start_line or 1)

        for n in sorted_nodes:
            content = n.content
            blocks = []
            last_end = 0

            for match in re.finditer(MARKDOWN_IMAGE_PATTERN, content):
                start, end = match.span()
                image_path = match.group(1)
                path_segments = image_path.split("/")
                container = path_segments[0]
                blob_path = "/".join(path_segments[1:])

                if start > last_end:
                    blocks.append(TextBlock(text=content[last_end:start].strip()))

                image_url = AnonymousFileAccessService.generate_sas_url(container, blob_path, lifetime_hours=1)
                blocks.append(ImageBlock(url=image_url))
                last_end = end

            if last_end < len(content):
                blocks.append(TextBlock(text=content[last_end:].strip()))

            text_blocks.extend(blocks)

        text_blocks.append(TextBlock(text="</REFERENCE_DOCUMENT>\n"))
        text_blocks.append(TextBlock(text="\n---\n"))

        blocks.extend(text_blocks)

    blocks.append(TextBlock(text=prompt_parts[1]))

    return ChatMessage(
        role=MessageRole.SYSTEM,
        content=blocks,
    )
