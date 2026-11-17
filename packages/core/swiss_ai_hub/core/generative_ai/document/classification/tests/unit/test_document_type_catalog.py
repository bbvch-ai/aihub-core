"""The catalog is the one place types and attributes are defined; these tests keep everything built from it, and the
model's answer schema, consistent with it."""

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_prompt import (
    DocumentClassificationPrompt,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.document_type_catalog import DocumentTypeCatalog
from swiss_ai_hub.core.persistence.rag.vectors import node_metadata

pytestmark = pytest.mark.unit


def test_every_type_has_exactly_one_definition_and_other_exists() -> None:
    defined = [definition.type for definition in DocumentTypeCatalog.TYPES]

    assert sorted(defined) == sorted(DocumentType)
    assert DocumentType.OTHER in defined


def test_every_attribute_has_exactly_one_definition() -> None:
    defined = [definition.attribute for definition in DocumentTypeCatalog.ATTRIBUTES]

    assert sorted(defined) == sorted(DocumentAttribute)


def test_a_type_overrides_only_the_meaning_of_attributes_that_apply_to_it() -> None:
    for definition in DocumentTypeCatalog.TYPES:
        assert set(definition.meanings) <= set(definition.attributes), definition.type


def test_a_derived_attribute_applies_only_with_its_sources() -> None:
    for type_definition in DocumentTypeCatalog.TYPES:
        for attribute in DocumentTypeCatalog.applicable(type_definition.type):
            assert set(attribute.derived_from) <= set(type_definition.attributes), attribute.attribute


def test_other_has_no_attributes() -> None:
    assert DocumentTypeCatalog.applicable(DocumentType.OTHER) == []


def test_the_answer_schema_has_one_field_per_attribute_the_model_fills() -> None:
    extracted = {definition.key for definition in DocumentTypeCatalog.extracted_attributes()}
    answer_attributes = set(DocumentClassificationAnswer.model_fields) - {"document_type", "secondary_types"}

    assert answer_attributes == extracted


def test_the_answer_schema_requires_every_field_so_strict_output_accepts_it() -> None:
    schema = DocumentClassificationAnswer.model_json_schema()

    assert set(schema["required"]) == set(schema["properties"])


def test_metadata_keys_are_unique_and_do_not_collide_with_platform_keys() -> None:
    keys = DocumentTypeCatalog.metadata_keys()
    classification_keys = {
        node_metadata.DOCUMENT_TYPE,
        node_metadata.DOCUMENT_TYPES,
        node_metadata.DOCUMENT_CLASSIFICATION_VERSION,
        node_metadata.DOCUMENT_TYPE_VERSION,
        node_metadata.DOCUMENT_NORMALIZER_VERSION,
    }
    platform_keys = {
        value for name, value in vars(node_metadata).items() if name.isupper() and isinstance(value, str)
    } - classification_keys

    assert len(keys) == len(set(keys))
    assert all(isinstance(key, str) and type(key) is str for key in keys)
    assert not set(keys) & platform_keys


def _with_other_at_version(version: int) -> tuple:
    return tuple(
        definition.model_copy(update={"version": version}) if definition.type == DocumentType.OTHER else definition
        for definition in DocumentTypeCatalog.TYPES
    )


def _current(document_type: DocumentType) -> dict:
    return {
        "classification_version": DocumentTypeCatalog.VERSION,
        "document_type": document_type.value,
        "type_version": DocumentTypeCatalog.type_definition(document_type).version,
    }


def test_every_type_starts_at_version_one_or_later() -> None:
    assert all(definition.version >= 1 for definition in DocumentTypeCatalog.TYPES)


def test_a_document_classified_with_the_current_versions_is_not_classified_again() -> None:
    assert not DocumentTypeCatalog.needs_classification(**_current(DocumentType.INVOICE))
    assert not DocumentTypeCatalog.needs_classification(**_current(DocumentType.OTHER))


@pytest.mark.parametrize(
    "stored",
    [
        {"classification_version": None, "document_type": None, "type_version": None},
        {**_current(DocumentType.INVOICE), "classification_version": DocumentTypeCatalog.VERSION - 1},
        {**_current(DocumentType.INVOICE), "type_version": None},
        {**_current(DocumentType.INVOICE), "type_version": 0},
        {**_current(DocumentType.INVOICE), "document_type": "credit_note_removed_since"},
    ],
    ids=["unclassified", "older-catalog", "no-type-version", "older-type", "unknown-type"],
)
def test_an_outdated_or_unknown_classification_is_classified_again(stored: dict) -> None:
    assert DocumentTypeCatalog.needs_classification(**stored)


def test_adding_a_type_raises_others_version_and_redoes_only_the_documents_marked_other(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoice, other = _current(DocumentType.INVOICE), _current(DocumentType.OTHER)
    monkeypatch.setattr(DocumentTypeCatalog, "TYPES", _with_other_at_version(other["type_version"] + 1))

    assert DocumentTypeCatalog.needs_classification(**other)
    assert not DocumentTypeCatalog.needs_classification(**invoice)


def test_value_keys_leave_out_only_the_copied_text() -> None:
    value_keys = DocumentTypeCatalog.value_keys()

    assert "document_date" in value_keys
    assert "document_period_start" in value_keys
    assert not [key for key in value_keys if key.endswith("_raw")]


def test_the_prompt_names_every_type_and_every_attribute_the_model_fills() -> None:
    messages = DocumentClassificationPrompt.prompt_template().format_messages(
        **DocumentClassificationPrompt.arguments("scan.pdf", "text")
    )
    system = messages[0].content

    for document_type in DocumentType:
        assert f'<type name="{document_type}">' in system
    for definition in DocumentTypeCatalog.extracted_attributes():
        assert f'<attribute name="{definition.key}">' in system
    assert "The issue date (Rechnungsdatum)" in system
