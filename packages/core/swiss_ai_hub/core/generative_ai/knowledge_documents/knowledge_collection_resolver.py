import asyncio

from mongoengine import DoesNotExist

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_not_found_error import (
    KnowledgeCollectionNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity


class KnowledgeCollectionResolver:
    """Resolves collections to the database their documents live in, shared by every reader of knowledge documents.

    A collection that does not exist or is being deleted raises instead of being skipped, so a caller never presents
    results from fewer collections than it was given as complete.
    """

    @staticmethod
    def same(first: BucketNamespacePair, second: BucketNamespacePair) -> bool:
        return first.bucket_name == second.bucket_name and first.namespace_name == second.namespace_name

    @staticmethod
    async def resolve_all(collections: list[BucketNamespacePair]) -> list[ResolvedKnowledgeCollection]:
        unique = {(pair.bucket_name, pair.namespace_name): pair for pair in collections}
        return [await asyncio.to_thread(KnowledgeCollectionResolver.resolve, pair) for pair in unique.values()]

    @staticmethod
    def resolve(collection: BucketNamespacePair) -> ResolvedKnowledgeCollection:
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
