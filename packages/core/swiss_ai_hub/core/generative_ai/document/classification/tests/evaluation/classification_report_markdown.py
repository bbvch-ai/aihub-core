from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_kind import CaseKind
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report import (
    ClassificationReport,
)


class ClassificationReportMarkdown:
    """The report as the PR posts it: the measures against their targets, then what cost a point.

    Only a sample of made-up documents may name its cases: a real document's filename, parties and amounts are the
    customer's, and a PR is not the place for them. Without `with_cases` the report counts misclassifications per kind
    instead, and the attribute table already counts wrong and guessed values per key.
    """

    @classmethod
    def render(cls, report: ClassificationReport, *, with_cases: bool) -> str:
        details = (
            [cls._misclassified(report), cls._costly_values(report)]
            if with_cases
            else [cls._misclassified_counts(report)]
        )
        return "\n\n".join([cls._summary(report), cls._attributes(report), *details])

    @classmethod
    def _misclassified_counts(cls, report: ClassificationReport) -> str:
        lines = [
            f"- {kind}: {count} of {len(report.of_kind(kind))}"
            for kind in CaseKind
            if (count := sum(result.predicted_type != result.case.expected_type for result in report.of_kind(kind)))
        ]
        return "**Misclassified, per kind**\n\n" + ("\n".join(lines) if lines else "none")

    @classmethod
    def _summary(cls, report: ClassificationReport) -> str:
        calls = len(report.results) or 1
        seconds = sorted(result.seconds for result in report.results) or [0.0]
        counts = {kind: len(report.of_kind(kind)) for kind in CaseKind}
        missed = report.missed_targets()
        return "\n".join(
            [
                f"### {report.name}: {len(report.results)} documents, model `{report.model}`",
                "",
                "| Measure | Value | Target |",
                "| --- | --- | --- |",
                f"| Invoice recall ({counts[CaseKind.INVOICE] + counts[CaseKind.BOUNDARY_INVOICE]}) "
                f"| {report.invoice_recall:.1%} | ≥ {report.MIN_INVOICE_RECALL:.0%} |",
                f"| Precision on documents resembling invoices ({counts[CaseKind.HARD_NEGATIVE]}) "
                f"| {report.hard_negative_precision:.1%} | ≥ {report.MIN_HARD_NEGATIVE_PRECISION:.0%} |",
                f"| Plainly different documents kept out ({counts[CaseKind.EASY_NEGATIVE]}) "
                f"| {report.easy_negative_precision:.1%} | – |",
                f"| Invoice precision overall | {report.invoice_precision:.1%} | – |",
                f"| Failed calls | {sum(result.error is not None for result in report.results)} | – |",
                f"| Tokens per document (prompt / completion) | {report.prompt_tokens // calls} / "
                f"{report.completion_tokens // calls} | – |",
                f"| Seconds per document (median / max) | {seconds[len(seconds) // 2]:.1f} / {seconds[-1]:.1f} | – |",
                "",
                "**Targets met.**" if not missed else "**Targets missed:** " + "; ".join(missed),
            ]
        )

    @classmethod
    def _attributes(cls, report: ClassificationReport) -> str:
        header = "| Attribute | " + " | ".join(outcome.value for outcome in AttributeOutcome) + " |"
        rows = [header, "| --- |" + " --- |" * len(AttributeOutcome)]
        for key, shares in report.attribute_shares().items():
            rows.append(f"| `{key}` | " + " | ".join(f"{shares[outcome]:.0%}" for outcome in AttributeOutcome) + " |")
        return "\n".join(rows)

    @classmethod
    def _misclassified(cls, report: ClassificationReport) -> str:
        lines = [
            f"- `{result.case.id}` ({result.case.kind}): {result.predicted_type or 'failed'}, "
            f"expected {result.case.expected_type}" + (f" — {result.error}" if result.error else "")
            for result in report.results
            if result.predicted_type != result.case.expected_type
        ]
        return "**Misclassified**\n\n" + ("\n".join(lines) if lines else "none")

    @classmethod
    def _costly_values(cls, report: ClassificationReport) -> str:
        lines = [
            f"- `{result.case.id}` `{key}`: {outcome}, expected `{result.case.expected[key]}`, "
            f"stored `{result.metadata.get(key)}`"
            for result in report.results
            if result.predicted_type == DocumentType.INVOICE
            for key, outcome in result.outcomes().items()
            if outcome in (AttributeOutcome.WRONG, AttributeOutcome.GUESSED)
        ]
        return "**Wrong or guessed values**\n\n" + ("\n".join(lines) if lines else "none")
