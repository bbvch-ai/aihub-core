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
    "document_valid_until": None,
    "document_notice_period": None,
    "document_service_levels": None,
    "document_product": None,
    "document_participants": None,
    "document_jurisdiction": None,
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


def test_an_e_mail_address_is_not_stored_as_a_name_but_keeps_its_text() -> None:
    text = _INVOICE + "\nAn: buchhaltung@muster.example\n"

    values = _classified(text, document_recipient="buchhaltung@muster.example").values

    assert values["document_recipient"] is None
    assert values["document_recipient_raw"] == "buchhaltung@muster.example"
    assert values["document_parties"] == ["Hooli AG"]


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


_SLA = """# Nebelhorn Hosting AG
Industriestrasse 9, 6300 Zug

Kunde: Seeblick Hotel AG, Uferweg 2, 6006 Luzern

## Service Level Agreement SLA-2025-14
Anhang 2 zum Rahmenvertrag RV-2024-031 · Zug, 2. Mai 2025

Laufzeit: 1. Juni 2025 bis 31. Mai 2027
Kündigungsfrist: 6 Monate auf Ende der Laufzeit

| Service Level | Zusage |
|---|---|
| Verfügbarkeit | 99,9 % pro Monat |
| Reaktionszeit Priorität 1 | 30 Minuten |
"""


def test_a_service_level_agreement_stores_its_own_attributes_and_none_of_an_invoice() -> None:
    answer = {
        **_ANSWER,
        "document_type": DocumentType.SERVICE_LEVEL_AGREEMENT,
        "document_date": "2. Mai 2025",
        "document_reference_number": "SLA-2025-14",
        "document_issuer": "Nebelhorn Hosting AG",
        "document_recipient": "Seeblick Hotel AG",
        "document_period": "1. Juni 2025 bis 31. Mai 2027",
        "document_notice_period": "6 Monate auf Ende der Laufzeit",
        "document_service_levels": ["99,9 % pro Monat", "Reaktionszeit Priorität 1 | 30 Minuten"],
        "document_related_references": ["RV-2024-031"],
        "document_total_amount": "CHF 12'496.36",
    }

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), _SLA).values

    assert values["document_period_start"] == "2025-06-01"
    assert values["document_period_end"] == "2027-05-31"
    assert values["document_notice_period"] == "6 Monate auf Ende der Laufzeit"
    assert values["document_service_levels"] == ["99,9 % pro Monat", "Reaktionszeit Priorität 1 | 30 Minuten"]
    assert values["document_related_references"] == ["RV-2024-031"]
    assert values["document_parties"] == ["Nebelhorn Hosting AG", "Seeblick Hotel AG"]
    assert "document_total_amount" not in values
    assert "document_due_date" not in values


_THREAD = """**Von:** Lea Brunner <lea.brunner@seeblick.example>
**Gesendet:** Dienstag, 4. März 2025 09:12
**An:** support@nebelhorn.example
**Betreff:** AW: Ausfall Buchungssystem, Ticket T-4471

Guten Morgen, das System läuft wieder. Danke! Lea Brunner, Seeblick Hotel AG

**Von:** Nebelhorn Hosting AG Support <support@nebelhorn.example>
**Gesendet:** Montag, 3. März 2025 18:40
**An:** Lea Brunner <lea.brunner@seeblick.example>
**Cc:** buchhaltung@seeblick.example

Wir haben die Störung behoben (SLA-2025-14).
"""

_THREAD_ANSWER: dict[str, Any] = {
    **{key: None for key in _ANSWER},
    "document_type": DocumentType.EMAIL_THREAD,
    "secondary_types": [],
    "document_date": "4. März 2025",
    "document_participants": [
        "Lea Brunner <lea.brunner@seeblick.example>",
        "Nebelhorn Hosting AG Support",
        "buchhaltung@seeblick.example",
        "Lea Brunner",
    ],
    "document_related_references": ["T-4471", "SLA-2025-14"],
    "document_issuer": "Nebelhorn Hosting AG",
}


def test_an_e_mail_thread_stores_its_participants_by_name_and_lists_them_as_parties() -> None:
    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**_THREAD_ANSWER), _THREAD).values

    assert values["document_date"] == "2025-03-04"
    assert values["document_participants"] == ["Lea Brunner", "Nebelhorn Hosting AG Support"]
    assert values["document_participants_raw"] == _THREAD_ANSWER["document_participants"]
    assert values["document_parties"] == ["Lea Brunner", "Nebelhorn Hosting AG Support"]
    assert values["document_related_references"] == ["T-4471", "SLA-2025-14"]
    assert "document_issuer" not in values


def test_a_thread_whose_participants_are_only_e_mail_addresses_has_no_participants_and_no_parties() -> None:
    answer = {**_THREAD_ANSWER, "document_participants": ["support@nebelhorn.example", "buchhaltung@seeblick.example"]}

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), _THREAD).values

    assert values["document_participants"] is None
    assert values["document_parties"] is None


def test_a_name_written_only_inside_an_e_mail_address_is_dropped_with_its_text_kept() -> None:
    answer = {**_THREAD_ANSWER, "document_participants": ["Buchhaltung", "Lea Brunner"]}

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), _THREAD).values

    assert values["document_participants"] == ["Lea Brunner"]
    assert values["document_participants_raw"] == ["Buchhaltung", "Lea Brunner"]


def test_a_name_copied_with_its_e_mail_address_keeps_the_name() -> None:
    text = _INVOICE + "\nAn: Muster Treuhand GmbH <buchhaltung@muster.example>\n"

    values = _classified(text, document_recipient="Muster Treuhand GmbH <buchhaltung@muster.example>").values

    assert values["document_recipient"] == "Muster Treuhand GmbH"
    assert values["document_parties"] == ["Hooli AG", "Muster Treuhand GmbH"]


def test_documentation_stores_the_product_it_documents() -> None:
    text = "# Benutzerhandbuch Kassensystem Orbis POS 4\nDok.-Nr. HB-ORB-040 · Ausgabe 03/2025\nKassenwerk AG"
    answer = {
        **{key: None for key in _ANSWER},
        "document_type": DocumentType.DOCUMENTATION,
        "secondary_types": [],
        "document_date": "03/2025",
        "document_reference_number": "HB-ORB-040",
        "document_issuer": "Kassenwerk AG",
        "document_product": "Kassensystem Orbis POS 4",
    }

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), text).values

    assert values["document_product"] == "Kassensystem Orbis POS 4"
    assert values["document_date"] == "2025-03-01"
    assert values["document_date_precision"] == "month"
    assert "document_parties" not in values


def test_a_contract_running_until_terminated_stores_its_start_alone() -> None:
    text = (
        "# Mietvertrag\nPilatus Logistik AG vermietet der Bergwerk Bau AG einen Lagerplatz.\n"
        "Das Mietverhältnis beginnt am 1. Juli 2025 und läuft auf unbestimmte Zeit.\nGerichtsstand ist Luzern."
    )
    answer = {
        **{key: None for key in _ANSWER},
        "document_type": DocumentType.CONTRACT,
        "secondary_types": [],
        "document_issuer": "Pilatus Logistik AG",
        "document_recipient": "Bergwerk Bau AG",
        "document_period": "beginnt am 1. Juli 2025 und läuft auf unbestimmte Zeit",
        "document_jurisdiction": "Luzern",
    }

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), text).values

    assert values["document_period_start"] == "2025-07-01"
    assert values["document_period_end"] is None
    assert values["document_jurisdiction"] == "Luzern"


@pytest.mark.parametrize(
    ("text", "stored"),
    [
        ("# SLA\nKestrel AG, Seefeldstrasse 101, 8008 Zürich\nZürich, 18 March 2026", None),
        ("# SLA\nKestrel AG, 8008 Zürich\nThe courts of Zürich have exclusive jurisdiction.", "Zürich"),
        ("# SLA\nKestrel AG, 8008 Zürich\n## 4. Gerichtsstand\nZürich", "Zürich"),
    ],
)
def test_a_jurisdiction_is_kept_only_where_a_clause_names_a_court(text: str, stored: str | None) -> None:
    answer = {
        **{key: None for key in _ANSWER},
        "document_type": DocumentType.SERVICE_LEVEL_AGREEMENT,
        "secondary_types": [],
        "document_jurisdiction": "Zürich",
    }

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), text).values

    assert values["document_jurisdiction"] == stored
    assert values["document_jurisdiction_raw"] == "Zürich"


def test_an_offer_reads_its_validity_as_a_date() -> None:
    text = "# Offerte OF-2025-221\nSchaffhausen, 20.02.2025 · gültig bis 31.03.2025\nOffertsumme CHF 3'080.85"
    answer = {
        **_ANSWER,
        "document_type": DocumentType.OFFER,
        "document_date": "20.02.2025",
        "document_reference_number": "OF-2025-221",
        "document_valid_until": "31.03.2025",
        "document_total_amount": "CHF 3'080.85",
    }

    values = DocumentClassification.from_answer(DocumentClassificationAnswer(**answer), text).values

    assert values["document_valid_until"] == "2025-03-31"
    assert values["document_valid_until_precision"] == "day"
    assert values["document_total_amount"] == 3080.85
    assert "document_due_date" not in values


def test_a_contract_with_a_service_level_annex_carries_both_types() -> None:
    classification = _classified(
        document_type=DocumentType.CONTRACT, secondary_types=[DocumentType.SERVICE_LEVEL_AGREEMENT]
    )

    assert classification.document_types == [DocumentType.CONTRACT, DocumentType.SERVICE_LEVEL_AGREEMENT]
    assert "document_service_levels" not in classification.values


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
