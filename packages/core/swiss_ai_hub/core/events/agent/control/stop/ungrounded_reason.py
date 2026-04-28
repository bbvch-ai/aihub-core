from enum import StrEnum


class UngroundedReason(StrEnum):
    """Why a RAG run terminated without producing an answer grounded in retrieved context."""

    CONTEXT_INSUFFICIENT = "context_insufficient"
    EXPERT_DECLINED = "expert_declined"
    EXPERT_ERRORED = "expert_errored"
    FEW_SHOT_FALLBACK = "few_shot_fallback"
