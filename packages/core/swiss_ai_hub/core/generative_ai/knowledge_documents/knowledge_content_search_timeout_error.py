class KnowledgeContentSearchTimeoutError(TimeoutError):
    """Raised when a content search does not finish within its time budget.

    The message says how to narrow the search, because a model that only learns it timed out tends to retry the same
    query.
    """

    def __init__(self, timeout_seconds: float) -> None:
        super().__init__(
            f"The content search did not finish within {timeout_seconds:g} s; narrow it with a path glob, fewer "
            "collections or a more specific pattern, and avoid nested repetition such as (a+)+"
        )
        self.timeout_seconds = timeout_seconds
