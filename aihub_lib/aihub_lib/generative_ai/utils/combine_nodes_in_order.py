import asyncio
import html
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock
from llama_index.core.prompts import RichPromptTemplate

from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    INSERTED_AT,
    LANGUAGE,
    NODE_CONTENT_TYPE_FIGURE,
    NODE_TYPE_CONTENT,
    SOURCE,
    UPDATED_AT,
    VERSION,
)

_ordered_headers = [H1, H2, H3, H4, H5, H6]

# Reuse a single S3 service instance to avoid repeated boto3 client creation
_s3_service: S3AnonymousFileAccessService | None = None


def _get_s3_service() -> S3AnonymousFileAccessService:
    """Get or create a singleton S3 service instance."""
    global _s3_service
    if _s3_service is None:
        _s3_service = S3AnonymousFileAccessService()
    return _s3_service


def _parse_image_path(image_path: str) -> tuple[str, str]:
    """Parse S3 image path into container and blob_path."""
    if image_path.startswith("s3://"):
        # S3 URI format: s3://bucket/path
        uri_parts = image_path[5:].split("/", 1)  # Remove 's3://' prefix
        return uri_parts[0], uri_parts[1] if len(uri_parts) > 1 else ""
    else:
        # Azure format: container/path
        return image_path.split("/", 1)


def _generate_presigned_url(container: str, blob_path: str) -> str:
    """Generate a presigned URL for an S3 object."""
    return _get_s3_service().generate_sas_url(container, blob_path, lifetime_hours=1)


def sanitize_metadata_value(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    sanitized_value = value.replace("'", "").strip()
    sanitized_value = html.escape(sanitized_value)
    return sanitized_value


async def combine_nodes_in_order(
    context_nodes: list[IngestedNode],
    t: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document: dict[str, list[IngestedNode]] = defaultdict(list)

    for context_node in context_nodes:
        key = context_node.source
        nodes_per_document[key].append(context_node)

    # Collect all figure nodes that need presigned URLs
    figure_nodes: list[tuple[str, str, str]] = []  # (node_id, container, blob_path)
    for nodes in nodes_per_document.values():
        for n in nodes:
            if n.content_type == NODE_CONTENT_TYPE_FIGURE:
                image_path = n.content.split("](")[-1][:-1]
                container, blob_path = _parse_image_path(image_path)
                figure_nodes.append((n.id, container, blob_path))

    # Generate all presigned URLs in parallel using a thread pool
    presigned_urls: dict[str, str] = {}
    if figure_nodes:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=min(len(figure_nodes), 10)) as executor:
            futures = [
                loop.run_in_executor(executor, _generate_presigned_url, container, blob_path)
                for node_id, container, blob_path in figure_nodes
            ]
            urls = await asyncio.gather(*futures)
            presigned_urls = {node_id: url for (node_id, _, _), url in zip(figure_nodes, urls)}

    context_blocks: list[ImageBlock | TextBlock] = []
    for key, nodes in nodes_per_document.items():
        if not nodes:
            continue

        node: IngestedNode = nodes[0]

        metadata_fields = {
            SOURCE: key,
            DOCUMENT_TITLE: node.document_title,
            LANGUAGE: node.language,
            VERSION: node.version,
            CREATED_AT: node.created_at,
            UPDATED_AT: node.updated_at,
            INSERTED_AT: node.inserted_at,
        }

        metadata_fields = {k: v for k, v in metadata_fields.items() if v is not None}

        metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())

        doc_header = f"<REFERENCE_DOCUMENT {metadata_string}>\n"

        context_blocks.append(TextBlock(text=doc_header))
        last_headings = [None] * len(_ordered_headers)
        sorted_nodes = sorted(nodes, key=lambda x: (x.section_start_line or 0, x.type == NODE_TYPE_CONTENT))

        for n in sorted_nodes:
            current_headings = [n.h1, n.h2, n.h3, n.h4, n.h5, n.h6]
            for i, heading in enumerate(current_headings):
                if heading and heading != last_headings[i]:
                    context_blocks.append(
                        TextBlock(
                            text=(
                                f"<{_ordered_headers[i]}>{html.escape(heading, quote=False)}</{_ordered_headers[i]}>\n"
                            )
                        )
                    )
                    last_headings[i] = heading
                    for j in range(i + 1, len(last_headings)):
                        last_headings[j] = None
                elif not heading:
                    last_headings[i] = None

            content = n.content

            if n.content_type == NODE_CONTENT_TYPE_FIGURE:
                # Use pre-generated presigned URL
                image_url = presigned_urls[n.id]
                context_blocks.append(ImageBlock(url=image_url))
            else:
                tag = n.type if n.type else NODE_TYPE_CONTENT
                context_blocks.append(TextBlock(text=(f"<{tag}>{html.escape(content, quote=False)}</{tag}>\n")))

        context_blocks.append(TextBlock(text="</REFERENCE_DOCUMENT>\n\n---\n"))

    if context_prompt:
        context_prompt_locale = t.extract(context_prompt, t.locale)
    else:
        context_prompt_locale = t("lib.prompt.rag.context_prompt")

    messages = RichPromptTemplate(
        template_str=context_prompt_locale,
    ).format_messages(context_blocks=context_blocks)

    return messages[0]
