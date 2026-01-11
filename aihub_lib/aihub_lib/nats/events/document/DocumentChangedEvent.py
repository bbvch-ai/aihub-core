from typing import Annotated, ClassVar

from openinference.semconv.trace import DocumentAttributes, OpenInferenceSpanKindValues, SpanAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class DocumentChangedEvent(SemanticEvent):
    """
    Event emitted when a document is created or modified.

    This event represents file creation or modification operations, typically from AI coding agents
    like OpenCode. It uses the Swiss AI-Hub document metadata structure for consistency with
    the RAG pipeline, while remaining flexible for agent-generated code files.

    The event is both:
    - A SemanticEvent (influences workflow, visible to user, and traced in Phoenix)
    - Compatible with OpenInference document conventions for observability
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.document_changed_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.document_changed_event.description"
    )

    # Core document identity
    document_id: Annotated[str, Field(description="Unique identifier for the document")]
    path: Annotated[str, Field(description="File path of the document")]

    # Content and metadata
    content: Annotated[str | None, Field(description="Full content of the document")] = None
    mime_type: Annotated[str | None, Field(description="MIME type of the document")] = None
    content_preview: Annotated[
        str | None, Field(description="Preview/excerpt of the content (first 200 chars)")
    ] = None

    # Operation metadata
    operation: Annotated[
        str, Field(description="Operation performed: 'created', 'modified', or 'changed' (unknown)")
    ] = "changed"
    namespace: Annotated[
        str | None, Field(description="Namespace or project context for the document")
    ] = None

    # Additional metadata
    metadata: Annotated[dict | None, Field(description="Additional custom metadata")] = None

    def to_semantic_convention(self) -> dict[str, str]:
        """
        Convert to OpenInference semantic conventions for document operations.

        Uses standard document attributes for tracing in Arize Phoenix and other
        OpenInference-compatible observability tools.
        """
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            DocumentAttributes.DOCUMENT_ID: self.document_id,
            DocumentAttributes.DOCUMENT_CONTENT: self.content,
            # Custom attributes for file operations
            "document.path": self.path,
            "document.operation": self.operation,
            "document.mime_type": self.mime_type,
            "document.namespace": self.namespace,
        }
        return {k: v for k, v in attributes.items() if v is not None}
