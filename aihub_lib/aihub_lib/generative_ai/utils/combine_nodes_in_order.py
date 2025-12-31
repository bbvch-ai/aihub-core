import asyncio
import html
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

_ordered_headers = [H1, H2, H3, H4, H5, H6]

# Thread-safe singleton for S3 service
_s3_service: S3AnonymousFileAccessService | None = None
_s3_service_lock = threading.Lock()


def _get_s3_service() -> S3AnonymousFileAccessService:
    """Get or create a thread-safe singleton S3 service instance."""
    global _s3_service
    if _s3_service is None:
        with _s3_service_lock:
            if _s3_service is None:
                _s3_service = S3AnonymousFileAccessService()
    return _s3_service


def _generate_presigned_url(content: str) -> str:
    """Generate a presigned URL for an S3 image from node content."""
    path = content.split("](")[-1][:-1].removeprefix("s3://")
    container, _, blob_path = path.partition("/")
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

    # Collect all figure nodes and generate presigned URLs in parallel
    figure_nodes = [
        (n.id, n.content)
        for nodes in nodes_per_document.values()
        for n in nodes
        if n.content_type == NODE_CONTENT_TYPE_FIGURE
    ]

    presigned_urls: dict[str, str] = {}
    if figure_nodes:
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=min(len(figure_nodes), 10)) as executor:
            futures = [loop.run_in_executor(executor, _generate_presigned_url, content) for _, content in figure_nodes]
            results = await asyncio.gather(*futures)
            for (node_id, _), url in zip(figure_nodes, results):
                presigned_urls[node_id] = url

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
                context_blocks.append(ImageBlock(url=presigned_urls[n.id]))
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
