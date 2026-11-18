"""The committed synthetic sample: enough documents of every type, complete labels, and labels that match their text.

A label typo would show up as a classifier error in every run, so the text labels are checked against the documents
here, without a model.
"""

from collections import Counter

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.raw_value_locator import RawValueLocator
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_corpus import (
    ClassificationCorpus,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.labelled_keys import LabelledKeys

pytestmark = pytest.mark.unit

_CASES = ClassificationCorpus.synthetic()
_TYPED = [case for case in _CASES if case.type != DocumentType.OTHER]
_TEXT_KEYS = ["document_reference_number", "document_issuer", "document_recipient", "document_notice_period"]
_LIST_KEYS = ["document_related_references", "document_service_levels"]
_MIN_CASES_PER_TYPE = 8


def test_every_type_has_enough_documents() -> None:
    counts = Counter(case.type for case in _CASES)

    assert {document_type: counts[document_type] for document_type in DocumentType} == {
        document_type: max(counts[document_type], _MIN_CASES_PER_TYPE) for document_type in DocumentType
    }


def test_invoices_keep_their_boundary_cases() -> None:
    assert Counter(case.type for case in _CASES)[DocumentType.INVOICE] >= 20


@pytest.mark.parametrize("case", _TYPED, ids=lambda case: case.id)
def test_every_typed_document_labels_every_value_key_of_its_type(case) -> None:
    assert set(case.expected) == set(LabelledKeys.value_keys(case.type))


@pytest.mark.parametrize("case", _TYPED, ids=lambda case: case.id)
def test_text_labels_are_written_in_their_document(case) -> None:
    for key in _TEXT_KEYS:
        if case.expected.get(key) is not None:
            assert RawValueLocator.appears_in(case.expected[key], case.text), f"{key}: {case.expected[key]}"
    for key in _LIST_KEYS:
        for item in case.expected.get(key) or []:
            assert RawValueLocator.appears_in(item, case.text), f"{key}: {item}"


def test_documents_of_no_type_carry_no_labels() -> None:
    assert not [case.id for case in _CASES if case.type == DocumentType.OTHER and case.expected]
