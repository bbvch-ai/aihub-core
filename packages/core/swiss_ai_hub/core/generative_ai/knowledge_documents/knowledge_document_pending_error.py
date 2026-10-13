from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair


class KnowledgeDocumentPendingError(LookupError):
    """Raised when a document exists but is still being ingested, so its stored text is missing or out of date.

    A re-synced file keeps its previous text while it is processed again; serving that text would hand out content
    the source no longer has.
    """

    def __init__(self, reference: str, collection: BucketNamespacePair) -> None:
        super().__init__(
            f"Document {reference!r} in {collection.bucket_name}/{collection.namespace_name} is still being ingested. "
            "Load it again once ingestion has finished."
        )
        self.reference = reference
        self.collection = collection
