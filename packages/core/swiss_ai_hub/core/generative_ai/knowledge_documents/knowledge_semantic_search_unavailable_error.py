class KnowledgeSemanticSearchUnavailableError(RuntimeError):
    """Raised when a ranking cannot be answered: Milvus is down or timed out, or the query cannot be embedded.

    A distinct type lets a caller with other ways to find documents, such as a content search, carry on with them
    instead of failing, without catching every error a ranking can raise.
    """

    def __init__(self, cause: Exception) -> None:
        super().__init__(f"The documents could not be ranked by meaning: {cause}")
