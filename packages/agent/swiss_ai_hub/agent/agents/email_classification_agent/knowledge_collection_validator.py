import asyncio
import logging

from mongoengine import DoesNotExist
from swiss_ai_hub.core.generative_ai import BucketNamespacePair
from swiss_ai_hub.core.imap import EmailClassificationSettings
from swiss_ai_hub.core.persistence import BucketEntity, NamespaceEntity

logger = logging.getLogger(__name__)


class KnowledgeCollectionValidator:
    """Checks the collections a category narrows retrieval to against the knowledge catalogue.

    A narrowed pair that nothing holds does not retrieve less, it retrieves *nothing*: `narrow_retrievers` keys the
    selection by bucket and drops every retriever left with no namespace in scope, and a RAG run over an empty
    context still returns an answer-shaped stop event, which the drafting step would then append to Drafts as a
    grounded reply. The form only offers collections the delegated agent is configured for, so this catches the
    selection that was valid when it was saved and whose collection has since been deleted.
    """

    @staticmethod
    async def validate(classification: EmailClassificationSettings) -> None:
        """Fail the run if a category narrows retrieval to a collection that no longer exists.

        Called before the first fetch, for the same reason `_validate_drafting` builds the prompt builder up front: a
        collection deleted since the profile was saved would otherwise be discovered after the whole batch has been
        classified, filed and paid for, and the drafts are unrecoverable by then because filing already consumed the
        mail.
        """
        for category in classification.categories:
            for pair in category.knowledge_namespaces or []:
                if not await KnowledgeCollectionValidator._holds(pair):
                    raise ValueError(
                        f"category {category.category!r} answers from the collection "
                        f"{pair.namespace_name!r} in {pair.bucket_name!r}, which the knowledge catalogue does not "
                        "hold — its replies would be answered from nothing"
                    )

    @staticmethod
    async def _holds(pair: BucketNamespacePair) -> bool:
        try:
            bucket = await asyncio.to_thread(BucketEntity.get_bucket_by_bucket_name, pair.bucket_name)
        except DoesNotExist:
            logger.warning("[draft] knowledge database %r does not exist", pair.bucket_name)
            return False

        namespaces = await asyncio.to_thread(NamespaceEntity.get_namespaces_by_bucket, str(bucket.id))
        return any(entity.namespace_name == pair.namespace_name for entity in namespaces)
