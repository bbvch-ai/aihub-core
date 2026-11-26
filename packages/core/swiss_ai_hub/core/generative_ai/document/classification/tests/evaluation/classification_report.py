from collections import Counter
from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_result import CaseResult


class ClassificationReport(BaseModel):
    """The measures #2481 agreed for invoices, applied to every type of the set (#2485).

    Per type: recall over the documents of that type, and precision over everything classified as it, so a type that
    swallows its look-alikes shows up as low precision. `OTHER` has no target: a document missed by a type already
    costs that type's recall. The attribute target holds per attribute over every document labelling it, as it did for
    invoices; with eight to ten documents a type, one slip would be 10% of a type, so the shares per type and attribute
    are reported to show where values go wrong, not held to the target.
    """

    MIN_RECALL: ClassVar[float] = 0.95
    MIN_PRECISION: ClassVar[float] = 0.95
    MAX_WRONG_OR_GUESSED: ClassVar[float] = 0.02

    name: Annotated[str, Field(description="Which sample this reports on")]
    model: Annotated[str, Field(description="Model that classified")]
    results: Annotated[list[CaseResult], Field(description="One result per case")]
    prompt_tokens: Annotated[int, Field(description="Prompt tokens over all calls")] = 0
    completion_tokens: Annotated[int, Field(description="Completion tokens over all calls")] = 0

    def of_type(self, document_type: DocumentType) -> list[CaseResult]:
        return [result for result in self.results if result.case.type == document_type]

    def predicted_as(self, document_type: DocumentType) -> list[CaseResult]:
        return [result for result in self.results if result.predicted_type == document_type]

    def types(self) -> list[DocumentType]:
        """The types the sample has documents of, in the catalog's order."""
        present = {result.case.type for result in self.results}
        return [document_type for document_type in DocumentType if document_type in present]

    def recall(self, document_type: DocumentType) -> float:
        results = self.of_type(document_type)
        return sum(result.is_correctly_typed for result in results) / len(results) if results else 1.0

    def precision(self, document_type: DocumentType) -> float:
        """Of everything classified as this type, the share that is of it."""
        predicted = self.predicted_as(document_type)
        return sum(result.is_correctly_typed for result in predicted) / len(predicted) if predicted else 1.0

    def attribute_shares(self) -> dict[tuple[DocumentType, str], dict[AttributeOutcome, float]]:
        counts: dict[tuple[DocumentType, str], Counter[AttributeOutcome]] = {}
        for result in self.results:
            for key, outcome in result.outcomes().items():
                counts.setdefault((result.case.type, key), Counter())[outcome] += 1
        return {
            type_and_key: {outcome: counter[outcome] / counter.total() for outcome in AttributeOutcome}
            for type_and_key, counter in counts.items()
        }

    def missed_targets(self) -> list[str]:
        missed = []
        for document_type in self.types():
            if document_type == DocumentType.OTHER:
                continue
            if self.recall(document_type) < self.MIN_RECALL:
                missed.append(f"{document_type} recall {self.recall(document_type):.1%} < {self.MIN_RECALL:.0%}")
            if self.precision(document_type) < self.MIN_PRECISION:
                missed.append(
                    f"{document_type} precision {self.precision(document_type):.1%} < {self.MIN_PRECISION:.0%}"
                )
        for key, costly in self.costly_shares().items():
            if costly > self.MAX_WRONG_OR_GUESSED:
                missed.append(f"{key}: wrong + guessed {costly:.1%} > {self.MAX_WRONG_OR_GUESSED:.0%}")
        return missed

    def costly_shares(self) -> dict[str, float]:
        """Per attribute, over every type: the share of labelled values stored wrong or guessed."""
        counts: dict[str, Counter[bool]] = {}
        for result in self.results:
            for key, outcome in result.outcomes().items():
                counts.setdefault(key, Counter())[outcome in (AttributeOutcome.WRONG, AttributeOutcome.GUESSED)] += 1
        return {key: counter[True] / counter.total() for key, counter in counts.items()}
