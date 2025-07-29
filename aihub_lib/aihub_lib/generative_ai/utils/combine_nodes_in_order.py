import html
from collections import defaultdict

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock
from llama_index.core.prompts import RichPromptTemplate

from aihub_lib.generative_ai.document.accessor.FileAccessServiceConfig import FileAccessServiceConfig
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


def sanitize_metadata_value(value: str) -> str:
    if not isinstance(value, str):
        return str(value)
    sanitized_value = value.replace("'", "").strip()
    sanitized_value = html.escape(sanitized_value)
    return sanitized_value


def _group_nodes_by_document(context_nodes: list[IngestedNode]) -> dict[str, list[IngestedNode]]:
    """Group nodes by their source document."""
    nodes_per_document: dict[str, list[IngestedNode]] = defaultdict(list)
    
    for context_node in context_nodes:
        key = context_node.source
        nodes_per_document[key].append(context_node)
    
    return nodes_per_document


def _create_document_metadata_fields(node: IngestedNode, key: str) -> dict[str, str]:
    """Create metadata fields for a document."""
    metadata_fields = {
        SOURCE: key,
        DOCUMENT_TITLE: node.document_title,
        LANGUAGE: node.language,
        VERSION: node.version,
        CREATED_AT: node.created_at,
        UPDATED_AT: node.updated_at,
        INSERTED_AT: node.inserted_at,
    }
    
    return {k: v for k, v in metadata_fields.items() if v is not None}


def _create_document_header(metadata_fields: dict[str, str]) -> str:
    """Create a document header with metadata."""
    metadata_string = " ".join(f"{k}='{sanitize_metadata_value(v)}'" for k, v in metadata_fields.items())
    return f"<REFERENCE_DOCUMENT {metadata_string}>\n"


def _update_headings_in_blocks(
    context_blocks: list[ImageBlock | TextBlock], 
    current_headings: list[str], 
    last_headings: list[str | None]
) -> None:
    """Update heading blocks and track last headings state."""
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


def _parse_image_path(image_path: str) -> tuple[str, str]:
    """Parse image path to extract container and blob path."""
    if image_path.startswith("s3://"):
        # S3 URI format: s3://bucket/path
        uri_parts = image_path[5:].split("/", 1)  # Remove 's3://' prefix
        container, blob_path = uri_parts[0], uri_parts[1] if len(uri_parts) > 1 else ""
    else:
        # Azure format: container/path
        container, blob_path = image_path.split("/", 1)
    
    return container, blob_path


def _process_node_content(context_blocks: list[ImageBlock | TextBlock], node: IngestedNode) -> None:
    """Process node content and add appropriate blocks."""
    content = node.content

    if node.content_type == NODE_CONTENT_TYPE_FIGURE:
        image_path = content.split("](")[-1][:-1]
        container, blob_path = _parse_image_path(image_path)
        
        file_access_config = FileAccessServiceConfig()
        image_url = file_access_config.service.generate_sas_url(container, blob_path, lifetime_hours=1)
        context_blocks.append(ImageBlock(url=image_url))
    else:
        tag = node.type if node.type else NODE_TYPE_CONTENT
        context_blocks.append(TextBlock(text=(f"<{tag}>{html.escape(content, quote=False)}</{tag}>\n")))


def _process_document_nodes(nodes: list[IngestedNode]) -> list[ImageBlock | TextBlock]:
    """Process all nodes for a single document."""
    context_blocks: list[ImageBlock | TextBlock] = []
    
    if not nodes:
        return context_blocks
    
    # Create document header
    node = nodes[0]
    metadata_fields = _create_document_metadata_fields(node, nodes[0].source)
    doc_header = _create_document_header(metadata_fields)
    context_blocks.append(TextBlock(text=doc_header))
    
    # Process nodes
    last_headings = [None] * len(_ordered_headers)
    sorted_nodes = sorted(nodes, key=lambda x: (x.section_start_line or 0, x.type == NODE_TYPE_CONTENT))
    
    for n in sorted_nodes:
        current_headings = [n.h1, n.h2, n.h3, n.h4, n.h5, n.h6]
        _update_headings_in_blocks(context_blocks, current_headings, last_headings)
        _process_node_content(context_blocks, n)
    
    context_blocks.append(TextBlock(text="</REFERENCE_DOCUMENT>\n\n---\n"))
    return context_blocks


def combine_nodes_in_order(
    context_nodes: list[IngestedNode],
    t: LocaleHandler,
    context_prompt: LocaleString = None,
) -> ChatMessage:
    nodes_per_document = _group_nodes_by_document(context_nodes)
    
    context_blocks: list[ImageBlock | TextBlock] = []
    for key, nodes in nodes_per_document.items():
        document_blocks = _process_document_nodes(nodes)
        context_blocks.extend(document_blocks)

    if context_prompt:
        context_prompt_locale = t.extract(context_prompt, t.locale)
    else:
        context_prompt_locale = t("lib.prompt.rag.context_prompt")

    messages = RichPromptTemplate(
        template_str=context_prompt_locale,
    ).format_messages(context_blocks=context_blocks)

    return messages[0]
