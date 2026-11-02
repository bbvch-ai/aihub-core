from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair


class KnowledgeCollectionNotFoundError(LookupError):
    """Raised when a collection passed to the reader does not exist or is being torn down.

    The whole call fails rather than skipping the collection: an agent that silently read fewer collections than it
    was configured with would return an answer that looks complete and is not.
    """

    def __init__(self, collection: BucketNamespacePair, reason: str) -> None:
        super().__init__(
            f"Knowledge collection {collection.namespace_name!r} in database {collection.bucket_name!r} {reason}"
        )
        self.collection = collection
        self.reason = reason
