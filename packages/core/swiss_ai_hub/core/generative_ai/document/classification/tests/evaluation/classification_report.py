from collections import Counter
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_kind import CaseKind
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_result import CaseResult


class ClassificationReport(BaseModel):
    """The measures #2481 reports, and whether they meet the targets the team agreed on.

    Recall counts every invoice, boundary cases included. Precision is measured where it is at risk: on documents that
    resemble invoices. Attribute shares are per key over the invoices labelling it.
    """

    MIN_INVOICE_RECALL: ClassVar[float] = 0.95
    MIN_HARD_NEGATIVE_PRECISION: ClassVar[float] = 0.95
    MAX_WRONG_OR_GUESSED: ClassVar[float] = 0.02

    name: Annotated[str, Field(description="Which sample this reports on")]
    model: Annotated[str, Field(description="Model that classified")]
    results: Annotated[list[CaseResult], Field(description="One result per case")]
    prompt_tokens: Annotated[int, Field(description="Prompt tokens over all calls")] = 0
    completion_tokens: Annotated[int, Field(description="Completion tokens over all calls")] = 0

    def of_kind(self, *kinds: CaseKind) -> list[CaseResult]:
        return [result for result in self.results if result.case.kind in kinds]

    @property
    def invoice_recall(self) -> float:
        return self._share(self.of_kind(CaseKind.INVOICE, CaseKind.BOUNDARY_INVOICE), DocumentType.INVOICE)

    @property
    def hard_negative_precision(self) -> float:
        """Share of documents resembling invoices that are kept out of the invoices."""
        return self._share(self.of_kind(CaseKind.HARD_NEGATIVE), DocumentType.OTHER)

    @property
    def easy_negative_precision(self) -> float:
        return self._share(self.of_kind(CaseKind.EASY_NEGATIVE), DocumentType.OTHER)

    @property
    def invoice_precision(self) -> float:
        """Of everything classified as an invoice, the share that is one."""
        predicted = [result for result in self.results if result.predicted_type == DocumentType.INVOICE]
        return sum(result.case.kind.is_invoice for result in predicted) / len(predicted) if predicted else 1.0

    def attribute_shares(self) -> dict[str, dict[AttributeOutcome, float]]:
        counts: dict[str, Counter[AttributeOutcome]] = {}
        for result in self.results:
            for key, outcome in result.outcomes().items():
                counts.setdefault(key, Counter())[outcome] += 1
        return {
            key: {outcome: counter[outcome] / counter.total() for outcome in AttributeOutcome}
            for key, counter in counts.items()
        }

    def missed_targets(self) -> list[str]:
        missed = []
        if self.of_kind(CaseKind.INVOICE, CaseKind.BOUNDARY_INVOICE) and self.invoice_recall < self.MIN_INVOICE_RECALL:
            missed.append(f"invoice recall {self.invoice_recall:.1%} < {self.MIN_INVOICE_RECALL:.0%}")
        if self.of_kind(CaseKind.HARD_NEGATIVE) and self.hard_negative_precision < self.MIN_HARD_NEGATIVE_PRECISION:
            missed.append(
                f"precision on documents resembling invoices {self.hard_negative_precision:.1%} "
                f"< {self.MIN_HARD_NEGATIVE_PRECISION:.0%}"
            )
        for key, shares in self.attribute_shares().items():
            costly = shares[AttributeOutcome.WRONG] + shares[AttributeOutcome.GUESSED]
            if costly > self.MAX_WRONG_OR_GUESSED:
                missed.append(f"{key}: wrong + guessed {costly:.1%} > {self.MAX_WRONG_OR_GUESSED:.0%}")
        return missed

    def _share(self, results: list[CaseResult], document_type: DocumentType) -> float:
        return sum(result.predicted_type == document_type for result in results) / len(results) if results else 1.0
