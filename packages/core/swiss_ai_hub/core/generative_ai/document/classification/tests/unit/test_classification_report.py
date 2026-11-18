"""How the evaluation counts: the outcome of one value, and the measures and targets over a sample."""

import json
from pathlib import Path
from typing import Any

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_comparison import (
    AttributeComparison,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
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
    assert AttributeComparison.outcome("document_issuer", expected, stored, raw) == outcome


@pytest.mark.parametrize(
    ("key", "expected", "stored", "outcome"),
    [
        ("document_notice_period", "trois mois avant son échéance", "trois mois", AttributeOutcome.CORRECT),
        ("document_notice_period", "3 Monate", "3 Monate auf Ende der Laufzeit.", AttributeOutcome.CORRECT),
        ("document_notice_period", "3 Monate", "6 Monate", AttributeOutcome.WRONG),
        (
            "document_service_levels",
            ["Verfügbarkeit 99,9 %", "Reaktionszeit 30 Minuten"],
            ["Reaktionszeit 30 Minuten.", "Die Verfügbarkeit 99,9 % pro Monat"],
            AttributeOutcome.CORRECT,
        ),
        (
            "document_service_levels",
            ["Verfügbarkeit 99,9 %", "Reaktionszeit 30 Minuten"],
            ["Verfügbarkeit 99,9 %"],
            AttributeOutcome.INCOMPLETE,
        ),
        (
            "document_service_levels",
            ["Verfügbarkeit 99,9 %"],
            ["Verfügbarkeit 99,9 %", "Backup täglich"],
            AttributeOutcome.WRONG,
        ),
    ],
)
def test_a_copied_passage_matches_when_either_contains_the_other(
    key: str, expected: Any, stored: Any, outcome: AttributeOutcome
) -> None:
    assert AttributeComparison.outcome(key, expected, stored, stored) == outcome


def _result(
    document_type: DocumentType,
    predicted: str | None,
    expected: dict | None = None,
    stored: dict | None = None,
    case_id: str | None = None,
) -> CaseResult:
    case = ClassificationCase(
        id=case_id or f"{document_type}-{predicted}", type=document_type, title="t", text="x", expected=expected or {}
    )
    metadata = {"document_type": predicted, **(stored or {})} if predicted else {}
    return CaseResult(case=case, metadata=metadata, error=None if predicted else "ValueError")


def _report(results: list[CaseResult]) -> ClassificationReport:
    return ClassificationReport(name="Test", model="m", results=results)


def test_recall_and_precision_are_measured_per_type() -> None:
    report = _report(
        [
            *[_result(DocumentType.INVOICE, "invoice") for _ in range(19)],
            _result(DocumentType.INVOICE, "credit_note"),
            *[_result(DocumentType.OFFER, "offer") for _ in range(9)],
            _result(DocumentType.ORDER, "offer"),
            _result(DocumentType.OTHER, None),
        ]
    )

    assert report.recall(DocumentType.INVOICE) == 0.95
    assert report.precision(DocumentType.OFFER) == 0.9
    assert report.recall(DocumentType.ORDER) == 0.0
    assert report.precision(DocumentType.CREDIT_NOTE) == 0.0
    assert report.recall(DocumentType.OTHER) == 0.0
    assert report.missed_targets() == [
        "offer precision 90.0% < 95%",
        "order recall 0.0% < 95%",
    ]


def test_a_type_without_documents_of_its_own_still_misses_precision_when_others_are_given_it() -> None:
    report = _report([_result(DocumentType.INVOICE, "receipt"), _result(DocumentType.INVOICE, "invoice")])

    assert report.types() == [DocumentType.INVOICE]
    assert report.precision(DocumentType.RECEIPT) == 0.0
    assert report.missed_targets() == ["invoice recall 50.0% < 95%"]


def test_an_attribute_misses_its_target_when_wrong_and_guessed_values_exceed_two_percent_over_all_types() -> None:
    good = {"document_issuer": "Hooli AG"}
    results = [_result(DocumentType.INVOICE, "invoice", good, good) for _ in range(48)]
    results.append(_result(DocumentType.INVOICE, "invoice", good, {"document_issuer": "Hooli Holding"}))
    results.append(_result(DocumentType.INVOICE, "invoice", {"document_issuer": None}, {"document_issuer": "Hooli AG"}))

    report = _report(results)

    shares = report.attribute_shares()[DocumentType.INVOICE, "document_issuer"]
    assert shares[AttributeOutcome.WRONG] == shares[AttributeOutcome.GUESSED] == 0.02
    assert report.missed_targets() == ["document_issuer: wrong + guessed 4.0% > 2%"]


def test_one_slip_in_a_small_type_is_reported_per_type_but_held_to_the_target_over_all_types() -> None:
    good = {"document_issuer": "Hooli AG"}
    results = [_result(DocumentType.INVOICE, "invoice", good, good) for _ in range(50)]
    results += [_result(DocumentType.OFFER, "offer", good, good) for _ in range(9)]
    results.append(_result(DocumentType.OFFER, "offer", good, {"document_issuer": "Hooli Holding"}))

    report = _report(results)

    assert report.attribute_shares()[DocumentType.OFFER, "document_issuer"][AttributeOutcome.WRONG] == 0.1
    assert report.costly_shares()["document_issuer"] == 1 / 60
    assert report.missed_targets() == []


def test_the_markdown_names_every_case_that_cost_a_point() -> None:
    expected = {"document_issuer": "Hooli AG"}
    report = _report(
        [
            _result(DocumentType.INVOICE, "invoice", expected, {"document_issuer": "Hooli Holding"}),
            _result(DocumentType.ORDER, "invoice"),
            _result(DocumentType.OTHER, None),
        ]
    )

    markdown = ClassificationReportMarkdown.render(report, with_cases=True)

    assert "**Targets missed:**" in markdown
    assert "| `order` | 1 | 0.0% | 100.0% |" in markdown
    assert "`document_issuer`: wrong, expected `Hooli AG`, stored `Hooli Holding`" in markdown
    assert "- `order-invoice`: invoice, expected order" in markdown
    assert "failed, expected other — ValueError" in markdown


def test_a_report_on_real_documents_counts_its_misses_without_naming_cases_or_values() -> None:
    expected = {"document_issuer": "Hooli AG"}
    report = _report(
        [
            _result(DocumentType.INVOICE, "invoice", expected, {"document_issuer": "Hooli Holding"}, "secret.pdf"),
            _result(DocumentType.ORDER, "invoice", case_id="confidential.pdf"),
        ]
    )

    markdown = ClassificationReportMarkdown.render(report, with_cases=False)

    assert "- order: 1 of 1" in markdown
    assert "Hooli" not in markdown
    assert "secret" not in markdown
    assert "confidential" not in markdown


@pytest.mark.asyncio
async def test_a_label_file_reads_text_files_next_to_it(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("# Rechnung RE-1", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Offerte", encoding="utf-8")
    labels = [
        {"file": "a.md", "type": "invoice", "expected": {"document_reference_number": "RE-1"}},
        {"file": "b.txt", "type": "offer"},
    ]
    label_file = tmp_path / "labels.jsonl"
    label_file.write_text("\n".join(json.dumps(label) for label in labels) + "\n", encoding="utf-8")

    cases = await ClassificationCorpus.from_label_file(label_file)

    assert [(case.id, case.text, case.expected) for case in cases] == [
        ("a.md", "# Rechnung RE-1", {"document_reference_number": "RE-1"}),
        ("b.txt", "Offerte", {}),
    ]


def test_a_label_with_a_key_its_type_does_not_have_is_refused() -> None:
    with pytest.raises(ValueError, match="not attributes of invoice"):
        ClassificationCase(id="x", type=DocumentType.INVOICE, title="t", text="x", expected={"document_date_raw": "x"})
    with pytest.raises(ValueError, match="not attributes of report"):
        ClassificationCase(id="y", type=DocumentType.REPORT, title="t", text="x", expected={"document_due_date": None})
    with pytest.raises(ValueError, match="not attributes of other"):
        ClassificationCase(id="z", type=DocumentType.OTHER, title="t", text="x", expected={"document_date": None})
