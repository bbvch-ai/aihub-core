import time

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_timeout_error import (
    KnowledgeContentSearchTimeoutError,
)


class KnowledgeSearchBudget:
    """One deadline for a whole content search, handed to every database query and regex match in turn.

    A budget per step would let a slow query spend it once per collection and per document.
    """

    def __init__(self, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self._deadline = time.monotonic() + timeout_seconds

    def remaining_seconds(self) -> float:
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise self.exhausted()
        return remaining

    def remaining_ms(self) -> int:
        """At least 1, because a `maxTimeMS` of 0 means no limit at all."""
        return max(1, int(self.remaining_seconds() * 1000))

    def exhausted(self) -> KnowledgeContentSearchTimeoutError:
        return KnowledgeContentSearchTimeoutError(self.timeout_seconds)
