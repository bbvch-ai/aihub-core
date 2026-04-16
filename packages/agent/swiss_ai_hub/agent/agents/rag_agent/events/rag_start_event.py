from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import StartEvent, UserUploadedFile
from swiss_ai_hub.core.generative_ai import BucketNamespacePair
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class RAGStartEvent(StartEvent):
    """
    Namespace-aware start event for the RAG agent.

    `RAGStartEvent` is intended for non-chat publishers: custom domain front-ends that run their own namespace
    selection UI, or other agents delegating to RAG via `AgentInTheLoop`.
    """

    _display_name: ClassVar = AgentLocaleString.from_i18n_path("agent.events.rag_start.name")
    _display_description: ClassVar = AgentLocaleString.from_i18n_path("agent.events.rag_start.description")

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

    @property
    def user_query(self) -> str:
        """
        Extracts the user query text from the chat history, returning the last user message content.
        Note: This only returns text content. Use last_user_message for full message with all blocks.
        """
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        return user_messages[-1].content if user_messages else ""

    @property
    def last_user_message(self) -> ChatMessage:
        """
        Extracts the complete last user message (with all blocks including images/audio) from chat history.
        Use this when passing messages to LLMs to preserve multimodal content.
        """
        user_messages = [msg for msg in self.messages if msg.role == MessageRole.USER]
        return user_messages[-1] if user_messages else ChatMessage(role=MessageRole.USER, content="")
