from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_classifier import DocumentClassifier
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK

pytestmark = pytest.mark.unit

_UNKNOWN: dict[str, Any] = dict.fromkeys(
    set(DocumentClassificationAnswer.model_fields) - {"document_type", "secondary_types"}
)


def _llm(answer: DocumentClassificationAnswer) -> Mock:
    llm = Mock()
    llm.astructured_predict = AsyncMock(return_value=answer)
    return llm


@pytest.mark.asyncio
async def test_the_model_reads_the_opening_and_end_and_its_copies_are_checked_against_the_whole_text() -> None:
    pages = ["# Rechnung RE-7", "Positionen", "mehr Positionen\n" + "| 2 | Kabel | 9.90 |\n" * 100, "Total CHF 100.00"]
    text = f"\n{PAGE_BREAK}\n".join(pages)
    answer = DocumentClassificationAnswer(
        **{**_UNKNOWN, "document_reference_number": "RE-7", "document_total_amount": "CHF 100.00"},
        document_type=DocumentType.INVOICE,
        secondary_types=[],
    )
    llm = _llm(answer)

    classification = await DocumentClassifier.classify(text, "re-7.pdf", llm)

    answer_model, _prompt = llm.astructured_predict.call_args.args
    prompt_arguments = llm.astructured_predict.call_args.kwargs
    assert answer_model is DocumentClassificationAnswer
    assert prompt_arguments["title"] == "re-7.pdf"
    assert "mehr Positionen" not in prompt_arguments["text"]
    assert "Total CHF 100.00" in prompt_arguments["text"]
    assert classification.document_type == DocumentType.INVOICE
    assert classification.values["document_total_amount"] == 100.0


@pytest.mark.asyncio
async def test_malformed_output_raises_for_the_caller_to_decide() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=ValueError("not JSON"))

    with pytest.raises(ValueError, match="not JSON"):
        await DocumentClassifier.classify("text", "doc.pdf", llm)
