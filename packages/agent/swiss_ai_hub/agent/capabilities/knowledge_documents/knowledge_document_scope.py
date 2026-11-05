import asyncio

from swiss_ai_hub.core.auth import AccessChecker
from swiss_ai_hub.core.events.agent import KnowledgeReference
from swiss_ai_hub.core.generative_ai import KnowledgeCollectionLabel, KnowledgeCollectionResolver

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope import KnowledgeToolScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_fields import KnowledgeDocumentFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext


class KnowledgeDocumentScope:
    """Computes what a run's document tools may touch, from the profile, the message's references and the user.

    The knowledge tool's own scope rule applies, so the documents a model can read are exactly the collections it could
    search; a profile that narrows references keeps `#` references from adding collections it does not list.
    """

    @staticmethod
    def of(
        config: KnowledgeDocumentFields,
        references: list[KnowledgeReference],
        access: AccessChecker | None,
        locale: str,
    ) -> KnowledgeDocumentRunScope:
        settings = config.knowledge_documents
        if settings.narrow_references:
            narrowed = KnowledgeToolScope.narrowed_collections(config.knowledge_tool, references, access)
            chosen, ignored = narrowed.collections, narrowed.ignored
        else:
            chosen, ignored = KnowledgeToolScope.collections(config.knowledge_tool, references, access), []
        return KnowledgeDocumentRunScope(
            collections=[KnowledgeDocumentScope._collection(reference, locale) for reference in chosen],
            restricting_glob=settings.path_glob or None,
            ignored=ignored,
        )

    @staticmethod
    async def for_tool(context: ToolContext) -> KnowledgeDocumentRunScope:
        config = context.agent_config
        if not isinstance(config, KnowledgeDocumentFields):
            raise TypeError(f"{type(config).__name__} lacks KnowledgeDocumentFields, which the document tools need")
        return await asyncio.to_thread(
            KnowledgeDocumentScope.of, config, context.knowledge_references, context.access, context.t.locale
        )

    @staticmethod
    def _collection(reference: KnowledgeReference, locale: str) -> KnowledgeDocumentCollection:
        return KnowledgeDocumentCollection(
            identifier=f"{reference.database}/{reference.namespace}",
            collection=KnowledgeCollectionResolver.pair_of(reference),
            label=KnowledgeCollectionLabel.of_reference(reference, locale),
        )
