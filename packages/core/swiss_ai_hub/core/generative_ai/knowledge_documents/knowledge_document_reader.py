import asyncio
import unicodedata
from typing import Annotated

from mongoengine import DoesNotExist

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_not_found_error import (
    KnowledgeCollectionNotFoundError,
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
from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

_COLLECTIONS_DESCRIPTION = "Collections the caller may read; nothing outside them is listed or loaded"


class KnowledgeDocumentReader:
    """Read access to the ingested documents of knowledge collections, independent of any agent.

    Callers pass the collections they may read, so deciding which those are stays with the caller's configuration.
    Every query is scoped to them, which is also what rejects an id or path from any other collection. Each knowledge
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
        for resolved in await KnowledgeDocumentReader._resolve_all(collections):
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
        for resolved in await KnowledgeDocumentReader._resolve_all(collections):
            ref_doc = await asyncio.to_thread(
                RefDoc.first_by_id_and_namespace, resolved.db_name, document_id, resolved.collection.namespace_name
            )
            if ref_doc is not None:
                return KnowledgeDocumentReader._to_document(ref_doc, resolved, document_id, start, end)
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
        """Load a document's parsed text by its path, which a model reproduces more reliably than a hex id."""
        resolved_collections = await KnowledgeDocumentReader._resolve_all(collections)
        target = next((resolved for resolved in resolved_collections if resolved.is_collection(collection)), None)
        if target is None:
            raise KnowledgeDocumentNotFoundError(path, collections)

        normalized_path = unicodedata.normalize("NFC", path).lstrip("/")
        ref_doc = await asyncio.to_thread(
            RefDoc.first_by_id_and_namespace,
            target.db_name,
            source_to_doc_id(target.source_for(normalized_path)),
            target.collection.namespace_name,
        )
        if ref_doc is None:
            ref_doc = await KnowledgeDocumentReader._find_by_normalized_path(target, normalized_path)
        if ref_doc is None:
            raise KnowledgeDocumentNotFoundError(path, collections)
        return KnowledgeDocumentReader._to_document(ref_doc, target, path, start, end)

    @staticmethod
    async def _find_by_normalized_path(resolved: ResolvedKnowledgeCollection, normalized_path: str) -> RefDoc | None:
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
            RefDoc.first_by_id_and_namespace, resolved.db_name, str(match.id), resolved.collection.namespace_name
        )

    @staticmethod
    def _to_document(
        ref_doc: RefDoc,
        resolved: ResolvedKnowledgeCollection,
        reference: str,
        start: int | None,
        end: int | None,
    ) -> KnowledgeDocument:
        if ref_doc.data.metadata.is_ingested is False or ref_doc.type_ == "placeholder":
            raise KnowledgeDocumentPendingError(reference, resolved.collection)
        return KnowledgeDocument.from_ref_doc(ref_doc, resolved, start, end)

    @staticmethod
    async def _resolve_all(collections: list[BucketNamespacePair]) -> list[ResolvedKnowledgeCollection]:
        unique = {(pair.bucket_name, pair.namespace_name): pair for pair in collections}
        return [await asyncio.to_thread(KnowledgeDocumentReader._resolve, pair) for pair in unique.values()]

    @staticmethod
    def _resolve(collection: BucketNamespacePair) -> ResolvedKnowledgeCollection:
        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(collection.bucket_name)
            namespace = NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), collection.namespace_name)
        except DoesNotExist as does_not_exist:
            raise KnowledgeCollectionNotFoundError(collection, "does not exist") from does_not_exist
        if bucket.deleting or namespace.deleting:
            raise KnowledgeCollectionNotFoundError(collection, "is being deleted")
        MongoConnectionRegistry.ensure_alias(bucket.db_name)
        return ResolvedKnowledgeCollection(
            collection=collection, db_name=bucket.db_name, folder_name=namespace.folder_name
        )
