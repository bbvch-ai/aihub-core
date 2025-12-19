from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent


class KnowledgeSource(BaseModel):
    """
    Represents a single knowledge source identified by bucket and namespace.

    Used by NamespaceSelectionAgent to specify which knowledge sources
    should be queried when delegating to RAGAgent.
    """

    bucket_name: Annotated[str, Field(description="The bucket/collection name containing the knowledge")]
    namespace_name: Annotated[str, Field(description="The namespace within the bucket")]
    display_name: Annotated[str | None, Field(description="Human-readable display name for the source")] = None


class RAGWithSourcesStartEvent(UserMessageEvent):
    """
    A start event for RAGAgent that includes pre-selected knowledge sources.

    Inherits all UserMessageEvent functionality (locale, user, messages, files)
    and adds knowledge source selection for dynamic retrieval configuration.

    ### Use Case
    When a NamespaceSelectionAgent has determined the relevant knowledge sources
    based on user query analysis or clarification, it invokes RAGAgent with this
    event to provide explicit source selection rather than relying on static config.

    ### Backward Compatibility
    RAGAgent can accept both UserMessageEvent (static config) and RAGWithSourcesStartEvent
    (dynamic sources). When this event is used, the knowledge_sources field takes
    precedence over the static retriever configuration.
    """

    _display_name: ClassVar[LocaleString] = LocaleString(
        en="RAG with Sources",
        de="RAG mit Quellen",
        fr="RAG avec sources",
        it="RAG con fonti",
    )
    _display_description: ClassVar[LocaleString] = LocaleString(
        en="Start RAG processing with pre-selected knowledge sources",
        de="RAG-Verarbeitung mit vorausgewählten Wissensquellen starten",
        fr="Démarrer le traitement RAG avec des sources de connaissances présélectionnées",
        it="Avvia l'elaborazione RAG con fonti di conoscenza preselezionate",
    )

    knowledge_sources: Annotated[
        list[KnowledgeSource],
        Field(description="Selected knowledge sources for retrieval", min_length=1),
    ]
    selection_reasoning: Annotated[
        str | None,
        Field(description="LLM reasoning for source selection (for transparency and observability)"),
    ] = None
