import html
from collections import defaultdict

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, TextBlock
from llama_index.core.prompts import RichPromptTemplate

from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.retrieval.rag_image_inline_settings import RagImageInlineSettings
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_service
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    INSERTED_AT,
    NODE_CONTENT_TYPE_FIGURE,
    NODE_TYPE_CONTENT,
    SOURCE,
    UPDATED_AT,
    VERSION,
)

_ordered_headers = [H1, H2, H3, H4, H5, H6]

# A record field rides in every document's header; a long one (a Confluence page's ancestors) is cut, not dropped.
MAX_RECORD_FIELD_CHARACTERS = 300


def sanitize_metadata_value(value: object) -> str:
    sanitized_value = str(value).replace("'", "").strip()
    sanitized_value = html.escape(sanitized_value)
    return sanitized_value


def _record_field_value(value: str | int | float | list[str]) -> str:
    text = ", ".join(value) if isinstance(value, list) else str(value)
    if len(text) <= MAX_RECORD_FIELD_CHARACTERS:
        return text
    return f"{text[:MAX_RECORD_FIELD_CHARACTERS].rstrip()}…"


def _document_header(node: IngestedNode) -> str:
    """The document's own attributes, then the fields of the record it was synced from (a Jira issue's status), so the
    model can answer about them. `language` is left out: ingestion detects none, so any value there is a default."""
    attributes = {
        "id": node.citation_id,
        SOURCE: node.source,
        DOCUMENT_TITLE: node.document_title,
        VERSION: node.version,
        CREATED_AT: node.created_at,
        UPDATED_AT: node.updated_at,
        INSERTED_AT: node.inserted_at,
    }
    attributes = {key: value for key, value in attributes.items() if value is not None}
    record_fields = {
        key: _record_field_value(value) for key, value in node.record_fields.items() if key not in attributes
    }
    return " ".join(
        f"{key}='{sanitize_metadata_value(value)}'" for key, value in {**attributes, **record_fields}.items()
    )


def combine_nodes_in_order(
    context_nodes: list[IngestedNode],
    t: LocaleHandler,
    context_prompt: LocaleString | None = None,
) -> ChatMessage:
    if context_prompt is None:
        context_prompt = LocaleString.from_i18n_path("lib.prompt.rag.context_prompt")

    # When inlining is enabled the figure URL is signed internally so the LiteLLM gateway
    # hook can fetch and base64-inline it; when disabled we fall back to the public
    # presigned URL (pre-inlining behaviour) for the provider to fetch directly.
    inline_enabled = RagImageInlineSettings().ENABLED

    nodes_per_document: dict[str, list[IngestedNode]] = defaultdict(list)

    for context_node in context_nodes:
        nodes_per_document[context_node.document_id].append(context_node)

    context_blocks: list[ImageBlock | TextBlock] = []
    for nodes in nodes_per_document.values():
        if not nodes:
            continue

        context_blocks.append(TextBlock(text=f"<REFERENCE_DOCUMENT {_document_header(nodes[0])}>\n"))
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
                image_path = content.split("](")[-1][:-1]

                if image_path.startswith("s3://"):
                    # S3 URI format: s3://bucket/path
                    uri_parts = image_path[5:].split("/", 1)  # Remove 's3://' prefix
                    container, blob_path = uri_parts[0], uri_parts[1] if len(uri_parts) > 1 else ""
                else:
                    # Azure format: container/path
                    container, blob_path = image_path.split("/", 1)

                # Internal-signed when inlining is on (the gateway hook fetches it
                # in-cluster and base64-inlines it, since the provider dereferences image
                # URLs server-side and cannot reach our storage); public-signed when off
                # (the provider fetches it directly). Either way the message stays tiny —
                # just the URL, no base64 rides on NATS events.
                image_url = create_s3_service().generate_sas_url(
                    container, blob_path, lifetime_hours=1, internal=inline_enabled
                )
                context_blocks.append(ImageBlock(url=image_url))
            else:
                tag = n.type if n.type else NODE_TYPE_CONTENT
                context_blocks.append(TextBlock(text=(f"<{tag}>{html.escape(content, quote=False)}</{tag}>\n")))

        context_blocks.append(TextBlock(text="</REFERENCE_DOCUMENT>\n\n---\n"))

    context_prompt_locale = t.extract(context_prompt, t.locale)

    messages = RichPromptTemplate(
        template_str=context_prompt_locale,
    ).format_messages(context_blocks=context_blocks)

    return messages[0]
