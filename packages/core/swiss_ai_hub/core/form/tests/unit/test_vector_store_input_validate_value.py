"""`VectorStoreInput.validate_value`: the save-time twin of `MilvusVectorStoreConfig`'s namespace-scope validator.

The API validates a save against a model rebuilt from the JSON Schema, which carries no Python validators, so this
is the only place an empty scope can be refused before it is stored and every run of the agent aborts (#1836).
"""

from typing import Any

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.form.elements.vector_store_input import VectorStoreInput
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig


def _messages(value: Any) -> list[str]:
    element = VectorStoreInput(label=LocaleString(en="Vector store"), name="vector_store")
    return element.validate_value("vector_store", value, LocaleHandler(locale="en"))


@pytest.mark.parametrize(
    ("index_namespaces", "all_namespaces"),
    [(["reports"], False), ([], True)],
    ids=["named namespaces", "all namespaces"],
)
def test_an_explicit_scope_is_accepted(index_namespaces: list[str], all_namespaces: bool):
    value = {"collection_name": "db", "index_namespaces": index_namespaces, "all_namespaces": all_namespaces}
    assert _messages(value) == []


@pytest.mark.parametrize(
    "value",
    [
        {"collection_name": "db", "index_namespaces": [], "all_namespaces": False},
        {"collection_name": "db", "index_namespaces": None},
        {"collection_name": "db"},
    ],
    ids=["empty list", "null list", "no scope keys"],
)
def test_an_empty_scope_is_rejected(value: dict[str, Any]):
    assert _messages(value) == ["Select at least one namespace to search, or enable all_namespaces."]


def test_naming_namespaces_and_all_at_once_is_rejected():
    value = {"collection_name": "db", "index_namespaces": ["a"], "all_namespaces": True}
    assert _messages(value) == ["Either name the namespaces to search or enable all_namespaces, not both."]


@pytest.mark.parametrize(
    "value",
    [
        {"collection_name": "db", "index_namespaces": [], "all_namespaces": False},
        {"collection_name": "db", "index_namespaces": ["a"], "all_namespaces": True},
    ],
    ids=["empty", "both"],
)
def test_the_message_matches_the_one_a_run_aborts_with(value: dict[str, Any]):
    with pytest.raises(ValidationError) as raised:
        MilvusVectorStoreConfig(dimensions=8, **value)
    assert _messages(value)[0] in str(raised.value)


@pytest.mark.parametrize(
    "value",
    [None, "db", {"index_namespaces": []}, {"collection_name": 3}, {"collection_name": "db", "index_namespaces": "a"}],
    ids=["null", "string", "no database", "non-string database", "non-list namespaces"],
)
def test_a_value_of_another_shape_is_left_to_schema_validation(value: Any):
    assert _messages(value) == []
