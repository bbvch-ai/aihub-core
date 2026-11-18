"""How the evaluation counts: the outcome of one value, and the measures and targets over a sample."""

import json
from pathlib import Path
from typing import Any

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_comparison import (
    AttributeComparison,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_kind import CaseKind
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_result import CaseResult
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_case import (
    ClassificationCase,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_corpus import (
    ClassificationCorpus,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report import (
    ClassificationReport,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_report_markdown import (
    ClassificationReportMarkdown,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("expected", "stored", "raw", "outcome"),
    [
        ("2025-03-14", "2025-03-14", "14. März 2025", AttributeOutcome.CORRECT),
        ("Hooli AG", "hooli  ag", "hooli  ag", AttributeOutcome.CORRECT),
        (12496.36, 12496.364, "CHF 12'496.36", AttributeOutcome.CORRECT),
        (["PO-3333", "LS-8812"], ["LS-8812", "PO-3333"], ["LS-8812", "PO-3333"], AttributeOutcome.CORRECT),
        (None, None, None, AttributeOutcome.CORRECT),
        ("2025-03-14", "2025-03-15", "15. März 2025", AttributeOutcome.WRONG),
        (None, "Hooli AG", "Hooli AG", AttributeOutcome.GUESSED),
        ("2025-03-14", None, None, AttributeOutcome.EMPTY),
        ("2025-03-14", None, "14.3.", AttributeOutcome.NOT_UNDERSTOOD),
    ],
)
def test_a_stored_value_is_compared_with_its_label(
    expected: Any, stored: Any, raw: Any, outcome: AttributeOutcome
) -> None:
    assert AttributeComparison.outcome(expected, stored, raw) == outcome


def _result(
    kind: CaseKind, predicted: str | None, expected: dict | None = None, stored: dict | None = None
) -> CaseResult:
    case = ClassificationCase(id=f"{kind}-{predicted}", kind=kind, title="t", text="x", expected=expected or {})
    metadata = {"document_type": predicted, **(stored or {})} if predicted else {}
    return CaseResult(case=case, metadata=metadata, error=None if predicted else "ValueError")


def _report(results: list[CaseResult]) -> ClassificationReport:
    return ClassificationReport(name="Test", model="m", results=results)


def test_recall_counts_boundary_invoices_and_precision_counts_lookalikes() -> None:
    report = _report(
        [
            *[_result(CaseKind.INVOICE, "invoice") for _ in range(19)],
            _result(CaseKind.BOUNDARY_INVOICE, "other"),
            *[_result(CaseKind.HARD_NEGATIVE, "other") for _ in range(9)],
            _result(CaseKind.HARD_NEGATIVE, "invoice"),
            _result(CaseKind.EASY_NEGATIVE, None),
        ]
    )

    assert report.invoice_recall == 0.95
    assert report.hard_negative_precision == 0.9
    assert report.easy_negative_precision == 0.0
    assert report.invoice_precision == 19 / 20
    assert report.missed_targets() == ["precision on documents resembling invoices 90.0% < 95%"]


def test_an_attribute_misses_its_target_when_wrong_and_guessed_values_exceed_two_percent() -> None:
    good = {"document_issuer": "Hooli AG"}
    results = [_result(CaseKind.INVOICE, "invoice", good, good) for _ in range(48)]
    results.append(_result(CaseKind.INVOICE, "invoice", good, {"document_issuer": "Hooli Holding"}))
    results.append(_result(CaseKind.INVOICE, "invoice", {"document_issuer": None}, {"document_issuer": "Hooli AG"}))

    report = _report(results)

    shares = report.attribute_shares()["document_issuer"]
    assert shares[AttributeOutcome.WRONG] == shares[AttributeOutcome.GUESSED] == 0.02
    assert report.missed_targets() == ["document_issuer: wrong + guessed 4.0% > 2%"]


def test_the_markdown_names_every_case_that_cost_a_point() -> None:
    expected = {"document_issuer": "Hooli AG"}
    report = _report(
        [
            _result(CaseKind.INVOICE, "invoice", expected, {"document_issuer": "Hooli Holding"}),
            _result(CaseKind.HARD_NEGATIVE, "invoice"),
            _result(CaseKind.EASY_NEGATIVE, None),
        ]
    )

    markdown = ClassificationReportMarkdown.render(report, with_cases=True)

    assert "**Targets missed:**" in markdown
    assert "`document_issuer`: wrong, expected `Hooli AG`, stored `Hooli Holding`" in markdown
    assert "(hard_negative): invoice, expected other" in markdown
    assert "failed, expected other — ValueError" in markdown


def test_a_report_on_real_documents_counts_its_misses_without_naming_cases_or_values() -> None:
    expected = {"document_issuer": "Hooli AG"}
    report = _report(
        [
            _result(CaseKind.INVOICE, "invoice", expected, {"document_issuer": "Hooli Holding"}),
            _result(CaseKind.HARD_NEGATIVE, "invoice"),
        ]
    )

    markdown = ClassificationReportMarkdown.render(report, with_cases=False)

    assert "- hard_negative: 1 of 1" in markdown
    assert "Hooli" not in markdown
    assert "invoice-invoice" not in markdown


@pytest.mark.asyncio
async def test_a_label_file_reads_text_files_next_to_it(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# Rechnung RE-1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Offerte", encoding="utf-8")
    labels = [
        {"file": "a.md", "kind": "invoice", "expected": {"document_reference_number": "RE-1"}},
        {"file": "b.txt", "kind": "hard_negative"},
    ]
    label_file = tmp_path / "labels.jsonl"
    label_file.write_text("\n".join(json.dumps(label) for label in labels) + "\n", encoding="utf-8")

    cases = await ClassificationCorpus.from_label_file(label_file)

    assert [(case.id, case.text, case.expected) for case in cases] == [
        ("a.md", "# Rechnung RE-1", {"document_reference_number": "RE-1"}),
        ("b.txt", "Offerte", {}),
    ]


def test_a_label_with_an_unknown_key_or_on_a_non_invoice_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown keys"):
        ClassificationCase(id="x", kind=CaseKind.INVOICE, title="t", text="x", expected={"document_date_raw": "x"})
    with pytest.raises(ValueError, match="only invoices"):
        ClassificationCase(id="y", kind=CaseKind.HARD_NEGATIVE, title="t", text="x", expected={"document_date": None})
