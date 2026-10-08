import asyncio
import unicodedata
from typing import Annotated

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_resolver import (
    KnowledgeCollectionResolver,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_not_found_error import (
    KnowledgeDocumentNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_pending_error import (
    KnowledgeDocumentPendingError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

_COLLECTIONS_DESCRIPTION = "Collections the caller may read; nothing outside them is listed or loaded"


class KnowledgeDocumentReader:
    """Read access to the ingested documents of knowledge collections, independent of any agent.

    Callers pass the collections the run may read, and the reader trusts that list: it must be the agent's configured
    collections narrowed to those the asking user may read (`AccessChecker.has_access_to_knowledge_namespace`), never a
    model's tool arguments, because a profile is checked only against whoever saved it. Every query is scoped to the
    list, which is what rejects an id or path from any other collection, so the only argument safe to take from a model
    is `collection` in `load_document_by_path`, which is checked against the list. Each knowledge
    database's document store is reached through its own connection alias, registered on first use, so this works from
    any process that has the default connection.
    """

    @staticmethod
    @trace_fn
    async def list_documents(
        collections: Annotated[list[BucketNamespacePair], _COLLECTIONS_DESCRIPTION],
    ) -> KnowledgeDocumentListing:
        """List every fully ingested document of the collections; documents still being ingested are left out."""
        summaries: list[KnowledgeDocumentSummary] = []
        for resolved in await KnowledgeCollectionResolver.resolve_all(collections):
            ref_docs = await asyncio.to_thread(
                RefDoc.list_ingested_summaries, resolved.db_name, resolved.collection.namespace_name
            )
            summaries.extend(KnowledgeDocumentSummary.from_ref_doc(ref_doc, resolved) for ref_doc in ref_docs)
        return KnowledgeDocumentListing.from_summaries(summaries)

    @staticmethod
    @trace_fn
    async def load_document(
        collections: Annotated[list[BucketNamespacePair], _COLLECTIONS_DESCRIPTION],
        document_id: Annotated[str, "Id of the document, as a listing returned it"],
        start: Annotated[int | None, "Offset of the first character to return; None for the beginning"] = None,
        end: Annotated[int | None, "Offset one past the last character to return; None for the end"] = None,
    ) -> KnowledgeDocument:
        """Load a document's parsed text by id, searching only the given collections."""
        for resolved in await KnowledgeCollectionResolver.resolve_all(collections):
            loaded = await asyncio.to_thread(
                RefDoc.first_with_text_range,
                resolved.db_name,
                document_id,
                resolved.collection.namespace_name,
                start,
                end,
            )
            if loaded is not None:
                return KnowledgeDocumentReader._to_document(loaded, resolved, document_id)
        raise KnowledgeDocumentNotFoundError(document_id, collections)

    @staticmethod
    @trace_fn
    async def load_document_by_path(
        collections: Annotated[list[BucketNamespacePair], _COLLECTIONS_DESCRIPTION],
        collection: Annotated[BucketNamespacePair, "Collection the path is relative to; must be one of `collections`"],
        path: Annotated[str, "Path relative to the collection, as a listing returned it"],
        start: Annotated[int | None, "Offset of the first character to return; None for the beginning"] = None,
        end: Annotated[int | None, "Offset one past the last character to return; None for the end"] = None,
    ) -> KnowledgeDocument:
        """Load a document's parsed text by its path, which a model reproduces more reliably than a hex id.

        Only the named collection is resolved, so a sibling collection being deleted does not fail the load.
        """
        if not any(KnowledgeCollectionResolver.same(allowed, collection) for allowed in collections):
            raise KnowledgeDocumentNotFoundError(path, collections)
        target = await asyncio.to_thread(KnowledgeCollectionResolver.resolve, collection)

        normalized_path = unicodedata.normalize("NFC", path).lstrip("/")
        loaded = await asyncio.to_thread(
            RefDoc.first_with_text_range,
            target.db_name,
            source_to_doc_id(target.source_for(normalized_path)),
            target.collection.namespace_name,
            start,
            end,
        )
        if loaded is None:
            loaded = await KnowledgeDocumentReader._find_by_normalized_path(target, normalized_path, start, end)
        if loaded is None:
            raise KnowledgeDocumentNotFoundError(path, collections)
        return KnowledgeDocumentReader._to_document(loaded, target, path)

    @staticmethod
    async def _find_by_normalized_path(
        resolved: ResolvedKnowledgeCollection, normalized_path: str, start: int | None, end: int | None
    ) -> tuple[RefDoc, int, int] | None:
        """Ids hash the stored path byte for byte, so a file stored with decomposed umlauts is only found by comparing
        normalised paths."""
        ref_docs = await asyncio.to_thread(
            RefDoc.list_ingested_summaries, resolved.db_name, resolved.collection.namespace_name
        )
        match = next(
            (
                ref_doc
                for ref_doc in ref_docs
                if unicodedata.normalize("NFC", resolved.relative_path(ref_doc.data.metadata.source)) == normalized_path
            ),
            None,
        )
        if match is None:
            return None
        return await asyncio.to_thread(
            RefDoc.first_with_text_range,
            resolved.db_name,
            str(match.id),
            resolved.collection.namespace_name,
            start,
            end,
        )

    @staticmethod
    def _to_document(
        loaded: tuple[RefDoc, int, int],
        resolved: ResolvedKnowledgeCollection,
        reference: str,
    ) -> KnowledgeDocument:
        ref_doc, text_length, start = loaded
        if ref_doc.data.metadata.is_ingested is False or ref_doc.type_ == "placeholder":
            raise KnowledgeDocumentPendingError(reference, resolved.collection)
        return KnowledgeDocument.from_text_range(ref_doc, resolved, text_length, start)
