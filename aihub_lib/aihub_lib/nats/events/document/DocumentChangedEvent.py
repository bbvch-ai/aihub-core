from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class DocumentChangedEvent(ControlAndDisplayEvent):
    """Event emitted when a document is created or modified by an AI coding agent."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.document_changed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.document_changed_event.description"
    )

    document_id: Annotated[str, Field(description="Unique identifier for the document")]
    path: Annotated[str, Field(description="File path of the document")]
    content: Annotated[str | None, Field(description="Full content of the document")] = None
    mime_type: Annotated[str | None, Field(description="MIME type of the document")] = None
    content_preview: Annotated[str | None, Field(description="Preview/excerpt of the content (first 200 chars)")] = None
    operation: Annotated[
        str, Field(description="Operation performed: 'created', 'modified', or 'changed' (unknown)")
    ] = "changed"
    namespace: Annotated[str | None, Field(description="Namespace or project context for the document")] = None
    metadata: Annotated[dict | None, Field(description="Additional custom metadata")] = None
