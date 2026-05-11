from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.generative_ai.retrievers.bucket_metadata_filters import BucketMetadataFilters
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RAGStartEvent(StartEvent):
    """
    Namespace-aware start event for the RAG agent.

    `RAGStartEvent` is intended for non-chat publishers: custom domain front-ends that run their own namespace
    selection UI, or other agents delegating to RAG via `AgentInTheLoop`.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_start_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_start_event.description")

    locale: Annotated[
        str,
        Field(description="The user's locale, guiding language or regional adaptations."),
    ] = LocaleHandler.DEFAULT_LOCALE
    user: Annotated[UserIdentity, Field(description="User on whose behalf the RAG run is executed.")]
    messages: Annotated[
        list[ChatMessage],
        Field(description="Chat history providing the context and the user query for retrieval."),
    ] = []
    files: Annotated[
        list[UserUploadedFile] | None,
        Field(description="Files uploaded alongside the query for additional context."),
    ] = None
    selected_namespaces: Annotated[
        list[BucketNamespacePair],
        Field(description="List of bucket-namespace pairs restricting RAG retrieval."),
    ]
    additional_filters: Annotated[
        list[BucketMetadataFilters] | None,
        Field(
            description=(
                "Per-bucket additional metadata filters (AND-combined with namespace filters). "
                "Filter keys must be listed in the target retriever's "
                "`MilvusVectorStoreConfig.allowed_metadata_filter_fields`. "
                "The reserved `namespace` key is not permitted here — use `selected_namespaces` instead."
            )
        ),
    ] = None
    org_memory_namespace: Annotated[
        str | None,
        Field(
            description=(
                "Optional namespace (department-level sub-scope) for organization-memory search. "
                "Must be in the agent profile's `tenant_namespaces` allow-list when that list is non-empty; "
                "raises otherwise. When omitted, the full configured list is searched."
            ),
        ),
    ] = None

    @property
    def user_query(self) -> str:
        """Last user message content as text. Use `last_user_message` for multimodal blocks."""
        return self.last_user_message.content or ""

    @property
    def last_user_message(self) -> ChatMessage:
        """Complete last user message including non-text blocks (images/audio)."""
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        return user_messages[-1] if user_messages else ChatMessage(role=MessageRole.USER, content="")
