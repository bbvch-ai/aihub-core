import asyncio
import html
import logging
import threading
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

logger = logging.getLogger(__name__)

_ordered_headers = [H1, H2, H3, H4, H5, H6]

# Thread-safe singleton for S3 service
_s3_service: S3AnonymousFileAccessService | None = None
_s3_service_lock = threading.Lock()


def _get_s3_service() -> S3AnonymousFileAccessService:
    """Get or create a thread-safe singleton S3 service instance."""
    global _s3_service
    if _s3_service is None:
        with _s3_service_lock:
            # Double-check locking pattern
            if _s3_service is None:
                _s3_service = S3AnonymousFileAccessService()
    return _s3_service


def _parse_image_path_from_content(content: str) -> str | None:
    """Extract image path from markdown figure content. Returns None if invalid format."""
    if "](" not in content:
        return None
    try:
        # Format: ![description](path)
        path = content.split("](")[-1]
        if path.endswith(")"):
            return path[:-1]
        return None
    except (IndexError, ValueError):
        return None


def _parse_s3_path(image_path: str) -> tuple[str, str]:
    """Parse S3 image path into container and blob_path."""
    path = image_path.removeprefix("s3://")
    container, _, blob_path = path.partition("/")
    return container, blob_path


def _generate_presigned_url(container: str, blob_path: str) -> str | None:
    """Generate a presigned URL for an S3 object. Returns None on failure."""
    try:
        return _get_s3_service().generate_sas_url(container, blob_path, lifetime_hours=1)
    except Exception as e:
        logger.warning(f"Failed to generate presigned URL for {container}/{blob_path}: {e}")
        return None


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
                image_path = _parse_image_path_from_content(n.content)
                if image_path is None:
                    logger.warning(f"Invalid figure content format for node {n.id}: {n.content[:100]}")
                    continue
                container, blob_path = _parse_s3_path(image_path)
                figure_nodes.append((n.id, container, blob_path))

    # Generate all presigned URLs in parallel using a thread pool
    presigned_urls: dict[str, str] = {}
    if figure_nodes:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=min(len(figure_nodes), 10)) as executor:
            futures = [
                loop.run_in_executor(executor, _generate_presigned_url, container, blob_path)
                for node_id, container, blob_path in figure_nodes
            ]
            results = await asyncio.gather(*futures, return_exceptions=True)
            for (node_id, _, _), result in zip(figure_nodes, results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to generate presigned URL for node {node_id}: {result}")
                elif result is not None:
                    presigned_urls[node_id] = result

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
                # Use pre-generated presigned URL, skip if not available
                image_url = presigned_urls.get(n.id)
                if image_url:
                    context_blocks.append(ImageBlock(url=image_url))
                else:
                    logger.warning(f"Skipping figure node {n.id}: no presigned URL available")
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
