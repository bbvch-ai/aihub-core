import asyncio
import logging

from mongoengine import DoesNotExist
from swiss_ai_hub.core.generative_ai import BucketNamespacePair
from swiss_ai_hub.core.imap import EmailClassificationSettings
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

logger = logging.getLogger(__name__)


class KnowledgeNamespaceResolver:
    """Turns a category's collection name into the bucket-namespace pairs a `RAGStartEvent` narrows retrieval by.

    A collection name alone does not identify anything: `narrow_retrievers` keys the selection by bucket, and a
    retriever whose bucket is missing from the selection is dropped. So a pair naming a bucket that has no such
    collection does not retrieve less, it retrieves *nothing* — and a RAG run over an empty context still returns an
    answer-shaped stop event, which the drafting agent would then append to Drafts as a grounded reply. Resolving
    against the catalogue instead of pairing blindly is what keeps that failure impossible rather than merely unlikely.
    """

    @staticmethod
    async def resolve(databases: list[str], namespace: str) -> list[BucketNamespacePair]:
        """The pairs for a namespace, one per configured database that actually holds it. Empty when none do."""
        pairs = []
        for database in databases:
            if await KnowledgeNamespaceResolver._holds(database, namespace):
                pairs.append(BucketNamespacePair(bucket_name=database, namespace_name=namespace))
        return pairs

    @staticmethod
    async def validate(classification: EmailClassificationSettings) -> None:
        """Fail the run if a category names a collection that does not exist in any configured database.

        Called before the first fetch, for the same reason `_validate_drafting` builds the prompt builder up front: a
        typo discovered at drafting time is discovered after the whole batch has been classified, filed and paid for,
        and the drafts are unrecoverable by then because filing already consumed the mail.
        """
        for category in classification.categories:
            if not category.knowledge_namespace:
                continue
            if not await KnowledgeNamespaceResolver.resolve(
                classification.knowledge_databases, category.knowledge_namespace
            ):
                raise ValueError(
                    f"category {category.category!r} is grounded in the collection "
                    f"{category.knowledge_namespace!r}, which none of the configured knowledge databases "
                    f"{classification.knowledge_databases} contains — its replies would be answered from nothing"
                )

    @staticmethod
    async def _holds(database: str, namespace: str) -> bool:
        try:
            bucket = await asyncio.to_thread(BucketEntity.get_bucket_by_bucket_name, database)
        except DoesNotExist:
            logger.warning("[draft] knowledge database %r does not exist — skipping it", database)
            return False

        namespaces = await asyncio.to_thread(NamespaceEntity.get_namespaces_by_bucket, str(bucket.id))
        return any(entity.namespace_name == namespace for entity in namespaces)
