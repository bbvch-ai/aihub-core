"""`InstanceConfigHelper.reject_invalid_values`: element-owned value rules applied at save time (#1836).

The form is the real one a RAG blueprint announces for its retrievers, round-tripped through the stored dict shape
the API reads back, so the field paths asserted here are the ones an admin sees.
"""

from typing import Annotated, Any

import pytest
from fastapi import HTTPException
from pydantic import Field, TypeAdapter
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, Form, FormkitElement
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.util.instance_config_helper import InstanceConfigHelper

EMPTY_SCOPE = "Select at least one namespace to search, or enable all_namespaces."


class _RetrieverBlueprintConfig(Form):
    retriever: Annotated[KnowledgeRetrieverConfig | None, Field(description="A single retriever")] = None
    retrievers: Annotated[list[KnowledgeRetrieverConfig], Field(description="A repeater of retrievers")] = []


def _elements() -> list[FormkitElement]:
    form = _RetrieverBlueprintConfig(
        retriever=KnowledgeRetrieverConfig.as_form(), retrievers=[KnowledgeRetrieverConfig.as_form()]
    )
    stored = [element.model_dump(by_alias=True) for element in form.to_formkit_form()]
    return TypeAdapter(list[ALL_FORM_OPTIONS]).validate_python(stored)


def _vector_store(namespaces: list[str], all_namespaces: bool = False) -> dict[str, Any]:
    return {"collection_name": "handbook", "index_namespaces": namespaces, "all_namespaces": all_namespaces}


def _reject(config: dict[str, Any] | None) -> None:
    InstanceConfigHelper.reject_invalid_values(_elements(), config, LocaleHandler(locale="en"))


def _detail(config: dict[str, Any]) -> str:
    with pytest.raises(HTTPException) as raised:
        _reject(config)
    assert raised.value.status_code == 400
    return raised.value.detail


def test_an_empty_scope_in_a_repeater_row_is_named_by_its_row():
    config = {"retrievers": [{"vector_store": _vector_store(["hr"])}, {"vector_store": _vector_store([])}]}

    assert _detail(config) == f"Configuration validation failed: retrievers.1.vector_store: {EMPTY_SCOPE}"


def test_the_numbered_dict_shape_of_a_repeater_is_walked_too():
    config = {"retrievers": {"0": {"vector_store": _vector_store([])}}}

    assert _detail(config) == f"Configuration validation failed: retrievers.0.vector_store: {EMPTY_SCOPE}"


def test_an_empty_scope_in_a_group_is_named_by_its_path():
    config = {"retriever": {"vector_store": _vector_store([])}}

    assert _detail(config) == f"Configuration validation failed: retriever.vector_store: {EMPTY_SCOPE}"


def test_every_rejected_value_is_reported_at_once():
    config = {
        "retriever": {"vector_store": _vector_store(["a"], all_namespaces=True)},
        "retrievers": [{"vector_store": _vector_store([])}],
    }

    detail = _detail(config)

    assert "retriever.vector_store: Either name the namespaces" in detail
    assert f"retrievers.0.vector_store: {EMPTY_SCOPE}" in detail


@pytest.mark.parametrize(
    "config",
    [
        None,
        {},
        {"retrievers": [{"vector_store": _vector_store(["hr", "legal"])}]},
        {"retrievers": [{"vector_store": _vector_store([], all_namespaces=True)}]},
        {"retriever": None, "retrievers": []},
    ],
    ids=["empty submission", "no retrievers", "named namespaces", "all namespaces", "cleared retrievers"],
)
def test_an_explicit_or_absent_scope_passes(config: dict[str, Any] | None):
    _reject(config)
