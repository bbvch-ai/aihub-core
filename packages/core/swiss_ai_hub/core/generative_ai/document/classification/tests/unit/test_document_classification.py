"""From the model's copied text to the stored metadata: the rules that keep "never guessed" true in code."""

from typing import Any

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_classification import DocumentClassification
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.generative_ai.document.classification.document_value_normalizer import DocumentValueNormalizer

pytestmark = pytest.mark.unit

_INVOICE = """# Hooli AG
Bahnhofstrasse 10, 8001 Zürich · MWST CHE-123.456.788

Muster Treuhand GmbH
z.Hd. Anna Meier

## Rechnung RE-2025-0412
Zürich, 14. März 2025
Lieferschein Nr. LS-8812 · Ihre Bestellung PO-3333

Leistungszeitraum: Februar 2025

**Total CHF 12'496.36**

Zahlbar innert 30 Tagen netto.
"""

_ANSWER: dict[str, Any] = {
    "document_type": DocumentType.INVOICE,
    "secondary_types": [],
    "document_date": "14. März 2025",
    "document_reference_number": "RE-2025-0412",
    "document_issuer": "Hooli AG",
    "document_issuer_tax_id": "CHE-123.456.788",
    "document_recipient": "Muster Treuhand GmbH",
    "document_total_amount": "CHF 12'496.36",
    "document_currency": None,
    "document_due_date": "Zahlbar innert 30 Tagen netto",
    "document_period": "Februar 2025",
    "document_related_references": ["LS-8812", "PO-3333"],
}


def _classified(text: str = _INVOICE, **changes: Any) -> DocumentClassification:
    return DocumentClassification.from_answer(DocumentClassificationAnswer(**{**_ANSWER, **changes}), text)


def test_an_invoice_is_stored_with_its_values_and_the_text_they_were_read_from() -> None:
    values = _classified().values

    assert values["document_date"] == "2025-03-14"
    assert values["document_date_precision"] == "day"
    assert values["document_date_raw"] == "14. März 2025"
    assert values["document_reference_number"] == "RE-2025-0412"
    assert values["document_issuer"] == "Hooli AG"
    assert values["document_issuer_tax_id"] == "CHE123456788"
    assert values["document_recipient"] == "Muster Treuhand GmbH"
    assert values["document_parties"] == ["Hooli AG", "Muster Treuhand GmbH"]
    assert values["document_total_amount"] == 12496.36
    assert values["document_period_start"] == "2025-02-01"
    assert values["document_period_end"] == "2025-02-28"
    assert values["document_period_precision"] == "month"
    assert values["document_related_references"] == ["LS-8812", "PO-3333"]


def test_every_key_of_an_invoice_is_stored_even_when_unknown() -> None:
    values = _classified(document_reference_number=None, document_related_references=None).values
    expected = {
        key for definition in DocumentTypeCatalog.applicable(DocumentType.INVOICE) for key in definition.stored_keys()
    }

    assert set(values) == expected
    assert values["document_reference_number"] is None


def test_payment_terms_without_a_date_keep_their_text_and_no_date() -> None:
    values = _classified().values

    assert values["document_due_date"] is None
    assert values["document_due_date_raw"] == "Zahlbar innert 30 Tagen netto"


def test_the_currency_is_read_from_the_total_when_not_copied_apart() -> None:
    assert _classified().values["document_currency"] == "CHF"


def test_a_value_that_is_not_in_the_document_is_dropped_with_its_text() -> None:
    values = _classified(document_issuer="Hooli Holding AG", document_related_references=["LS-8812", "X-1"]).values

    assert values["document_issuer"] is None
    assert values["document_issuer_raw"] is None
    assert values["document_parties"] == ["Muster Treuhand GmbH"]
    assert values["document_related_references"] == ["LS-8812"]


def test_a_tax_id_failing_its_check_keeps_its_text_but_no_value() -> None:
    text = _INVOICE.replace("CHE-123.456.788", "CHE-123.456.789")

    values = _classified(text, document_issuer_tax_id="CHE-123.456.789").values

    assert values["document_issuer_tax_id"] is None
    assert values["document_issuer_tax_id_raw"] == "CHE-123.456.789"


def test_the_documents_own_number_is_not_a_related_reference() -> None:
    values = _classified(document_related_references=["RE-2025-0412", "PO-3333"]).values

    assert values["document_related_references"] == ["PO-3333"]


def test_another_type_stores_no_invoice_attributes_whatever_the_model_filled() -> None:
    classification = _classified(document_type=DocumentType.OTHER)

    assert classification.values == {}
    assert classification.document_types == [DocumentType.OTHER]


def test_secondary_types_exclude_the_primary_type_and_other() -> None:
    classification = _classified(secondary_types=[DocumentType.INVOICE, DocumentType.OTHER, DocumentType.INVOICE])

    assert classification.document_types == [DocumentType.INVOICE]


def test_the_stored_metadata_carries_the_type_and_the_versions_it_was_made_with() -> None:
    metadata = _classified().to_metadata()

    assert metadata["document_type"] == "invoice"
    assert metadata["document_types"] == ["invoice"]
    assert metadata["document_classification_version"] == DocumentTypeCatalog.VERSION
    assert metadata["document_type_version"] == DocumentTypeCatalog.type_definition(DocumentType.INVOICE).version
    assert metadata["document_normalizer_version"] == DocumentValueNormalizer.VERSION
    assert set(metadata) <= set(DocumentTypeCatalog.metadata_keys())
    assert all(type(key) is str for key in metadata)


def test_renormalizing_reads_the_kept_copies_again_without_a_model() -> None:
    """A value a previous parser left empty is filled from the copy kept beside it (#2483)."""
    stored = _classified().to_metadata()
    stored["document_date"] = None
    stored["document_date_precision"] = None
    stored["document_normalizer_version"] = 0

    renormalized = DocumentClassification.renormalized(stored, _INVOICE)

    assert renormalized.document_type == DocumentType.INVOICE
    assert renormalized.values["document_date"] == "2025-03-14"
    assert renormalized.values["document_issuer"] == "Hooli AG"
    assert renormalized.to_metadata()["document_normalizer_version"] == DocumentValueNormalizer.VERSION


def test_renormalizing_keeps_the_secondary_types() -> None:
    stored = _classified().to_metadata()
    stored["document_types"] = ["invoice", "invoice"]

    assert DocumentClassification.renormalized(stored, _INVOICE).document_types == [DocumentType.INVOICE]


_SLASH_DATED = """# Imprimerie du Léman SA
Facture F-2026-344 du 05/11/2026
Total {total}
{extra}
"""


@pytest.mark.parametrize(
    ("total", "currency", "read"),
    [
        ("CHF 562.10", None, "2026-11-05"),
        ("562.10 EUR", None, "2026-11-05"),
        ("$562.10", None, None),
        ("USD 562.10", None, None),
        ("562.10", None, None),
    ],
    ids=["chf", "eur", "bare-dollar", "usd", "no-currency"],
)
def test_an_ambiguous_slash_date_is_day_first_only_on_a_non_dollar_document(
    total: str, currency: str | None, read: str | None
) -> None:
    text = _SLASH_DATED.format(total=total, extra="")
    classification = _classified(
        text,
        document_date="05/11/2026",
        document_total_amount=total,
        document_currency=currency,
        document_reference_number="F-2026-344",
        document_issuer="Imprimerie du Léman SA",
        document_issuer_tax_id=None,
        document_recipient=None,
        document_due_date=None,
        document_period=None,
        document_related_references=None,
    )

    assert classification.values["document_date"] == read
    assert classification.values["document_date_raw"] == "05/11/2026"


@pytest.mark.parametrize(
    ("total", "extra", "read"),
    [
        ("EUR 562.10", "Paid by transfer on 11/17/2026", "2026-05-11"),
        ("$562.10", "Delivered 17/11/2026", "2026-11-05"),
        ("CHF 562.10", "Delivered 17/11/2026, paid 11/18/2026", None),
    ],
    ids=["page-says-month-first", "page-says-day-first", "page-contradicts-itself"],
)
def test_the_documents_own_unambiguous_slash_dates_settle_the_order_before_its_currency(
    total: str, extra: str, read: str | None
) -> None:
    classification = _classified(
        _SLASH_DATED.format(total=total, extra=extra),
        document_date="05/11/2026",
        document_total_amount=total,
        document_currency=None,
        document_reference_number="F-2026-344",
        document_issuer="Imprimerie du Léman SA",
        document_issuer_tax_id=None,
        document_recipient=None,
        document_due_date=None,
        document_period=None,
        document_related_references=None,
    )

    assert classification.values["document_date"] == read
