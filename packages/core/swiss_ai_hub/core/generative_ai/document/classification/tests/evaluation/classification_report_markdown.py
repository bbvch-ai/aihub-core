from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report import (
    ClassificationReport,
)


class ClassificationReportMarkdown:
    """The report as the PR posts it: the measures against their targets, then what cost a point.

    Only a sample of made-up documents may name its cases: a real document's filename, parties and amounts are the
    customer's, and a PR is not the place for them. Without `with_cases` the report counts misclassifications per type
    instead, and the attribute table already counts wrong and guessed values per key.
    """

    @classmethod
    def render(cls, report: ClassificationReport, *, with_cases: bool) -> str:
        details = (
            [cls._misclassified(report), cls._costly_values(report)]
            if with_cases
            else [cls._misclassified_counts(report)]
        )
        return "\n\n".join([cls._summary(report), cls._types(report), cls._attributes(report), *details])

    @classmethod
    def _summary(cls, report: ClassificationReport) -> str:
        calls = len(report.results) or 1
        seconds = sorted(result.seconds for result in report.results) or [0.0]
        missed = report.missed_targets()
        return "\n".join(
            [
                f"### {report.name}: {len(report.results)} documents, model `{report.model}`",
                "",
                f"- Failed calls: {sum(result.error is not None for result in report.results)}",
                f"- Tokens per document (prompt / completion): {report.prompt_tokens // calls} / "
                f"{report.completion_tokens // calls}",
                f"- Seconds per document (median / max): {seconds[len(seconds) // 2]:.1f} / {seconds[-1]:.1f}",
                "",
                "**Targets met.**" if not missed else "**Targets missed:** " + "; ".join(missed),
            ]
        )

    @classmethod
    def _types(cls, report: ClassificationReport) -> str:
        rows = [
            f"| Type | Documents | Recall (≥ {report.MIN_RECALL:.0%}) | Precision (≥ {report.MIN_PRECISION:.0%}) |",
            "| --- | --- | --- | --- |",
        ]
        rows += [
            f"| `{document_type}` | {len(report.of_type(document_type))} | {report.recall(document_type):.1%} "
            f"| {report.precision(document_type):.1%} |"
            for document_type in report.types()
        ]
        return "\n".join(rows)

    @classmethod
    def _attributes(cls, report: ClassificationReport) -> str:
        header = "| Type | Attribute | " + " | ".join(outcome.value for outcome in AttributeOutcome) + " |"
        rows = [header, "| --- | --- |" + " --- |" * len(AttributeOutcome)]
        for (document_type, key), shares in report.attribute_shares().items():
            rows.append(
                f"| `{document_type}` | `{key}` | "
                + " | ".join(f"{shares[outcome]:.0%}" for outcome in AttributeOutcome)
                + " |"
            )
        return "\n".join(rows)

    @classmethod
    def _misclassified_counts(cls, report: ClassificationReport) -> str:
        lines = [
            f"- {document_type}: {count} of {len(report.of_type(document_type))}"
            for document_type in report.types()
            if (count := sum(not result.is_correctly_typed for result in report.of_type(document_type)))
        ]
        return "**Misclassified, per type**\n\n" + ("\n".join(lines) if lines else "none")

    @classmethod
    def _misclassified(cls, report: ClassificationReport) -> str:
        lines = [
            f"- `{result.case.id}`: {result.predicted_type or 'failed'}, expected {result.case.type}"
            + (f" — {result.error}" if result.error else "")
            for result in report.results
            if not result.is_correctly_typed
        ]
        return "**Misclassified**\n\n" + ("\n".join(lines) if lines else "none")

    @classmethod
    def _costly_values(cls, report: ClassificationReport) -> str:
        lines = [
            f"- `{result.case.id}` `{key}`: {outcome}, expected `{result.case.expected[key]}`, "
            f"stored `{result.metadata.get(key)}`"
            for result in report.results
            if result.is_correctly_typed
            for key, outcome in result.outcomes().items()
            if outcome in (AttributeOutcome.WRONG, AttributeOutcome.GUESSED)
        ]
        return "**Wrong or guessed values**\n\n" + ("\n".join(lines) if lines else "none")
