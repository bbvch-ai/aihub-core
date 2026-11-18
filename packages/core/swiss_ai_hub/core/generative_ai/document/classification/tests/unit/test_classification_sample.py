"""The committed synthetic sample: the size and mix #2481 asks for, complete labels, and labels that match their text.

A label typo would show up as a classifier error in every run, so the text labels are checked against the documents
here, without a model.
"""

from collections import Counter

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.raw_value_locator import RawValueLocator
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.case_kind import CaseKind
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_corpus import (
    ClassificationCorpus,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.labelled_keys import LabelledKeys

pytestmark = pytest.mark.unit

_CASES = ClassificationCorpus.synthetic()
_INVOICES = [case for case in _CASES if case.kind.is_invoice]
_TEXT_KEYS = ["document_reference_number", "document_issuer", "document_recipient"]


def test_the_sample_has_the_agreed_mix() -> None:
    kinds = Counter(case.kind for case in _CASES)

    assert kinds[CaseKind.HARD_NEGATIVE] >= 40
    assert kinds[CaseKind.EASY_NEGATIVE] >= 20
    assert kinds[CaseKind.BOUNDARY_INVOICE] >= 12


def test_every_invoice_labels_every_value_key() -> None:
    for case in _INVOICES:
        assert set(case.expected) == set(LabelledKeys.value_keys()), case.id


@pytest.mark.parametrize("case", _INVOICES, ids=lambda case: case.id)
def test_text_labels_are_written_in_their_document(case) -> None:
    for key in _TEXT_KEYS:
        if case.expected[key] is not None:
            assert RawValueLocator.appears_in(case.expected[key], case.text), f"{key}: {case.expected[key]}"
    for reference in case.expected["document_related_references"] or []:
        assert RawValueLocator.appears_in(reference, case.text), reference


def test_documents_resembling_invoices_cover_every_excluded_kind() -> None:
    prefixes = Counter(case.id.split("-")[0] for case in _CASES if case.kind == CaseKind.HARD_NEGATIVE)

    assert set(prefixes) >= {
        "offer",
        "order",
        "delivery",
        "receipt",
        "credit",
        "reminder",
        "statement",
        "proforma",
    }
