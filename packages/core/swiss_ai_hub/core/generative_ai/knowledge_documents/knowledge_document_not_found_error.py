from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair


class KnowledgeDocumentNotFoundError(LookupError):
    """Raised when a document id or path is not an ingested document of the collections the caller may read.

    A document that exists in some other collection is reported exactly like one that does not exist at all, so the
    error never tells a caller what lies outside its collections.
    """

    def __init__(self, reference: str, collections: list[BucketNamespacePair]) -> None:
        searched = ", ".join(f"{pair.bucket_name}/{pair.namespace_name}" for pair in collections) or "none"
        super().__init__(
            f"No ingested document {reference!r} in the collections {searched}. "
            "List the documents of these collections to get valid ids and paths."
        )
        self.reference = reference
        self.collections = collections
