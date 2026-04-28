from enum import StrEnum


class RAGFailureReason(StrEnum):
    """Why a RAG run failed to produce a useful answer."""

    CONTEXT_INSUFFICIENT = "context_insufficient"
    EXPERT_DECLINED = "expert_declined"
    EXPERT_ERRORED = "expert_errored"
    FEW_SHOT_REJECTED = "few_shot_rejected"
