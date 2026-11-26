import asyncio
import time

from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.document.classification.document_classifier import DocumentClassifier
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_result import CaseResult
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_case import (
    ClassificationCase,
)


class ClassificationEvaluation:
    """Classifies every case with a real model, side by side, and keeps going past a failed call.

    A failed call is a result, not a crash: in production it leaves the document unclassified, so the report counts it
    against recall or precision and names the error.
    """

    @classmethod
    async def run(cls, cases: list[ClassificationCase], llm: LLM, concurrency: int) -> list[CaseResult]:
        limiter = asyncio.Semaphore(concurrency)
        return await asyncio.gather(*(cls._classified(case, llm, limiter) for case in cases))

    @classmethod
    async def _classified(cls, case: ClassificationCase, llm: LLM, limiter: asyncio.Semaphore) -> CaseResult:
        async with limiter:
            started = time.monotonic()
            try:
                classification = await DocumentClassifier.classify(case.text, case.title, llm)
            except Exception as failure:  # noqa: BLE001 - a failed call is what the report must show, not a crash
                return CaseResult(
                    case=case,
                    metadata={},
                    # The type only: a provider's message can echo the request, i.e. a confidential document.
                    error=type(failure).__name__,
                    seconds=time.monotonic() - started,
                )
            return CaseResult(case=case, metadata=classification.to_metadata(), seconds=time.monotonic() - started)
