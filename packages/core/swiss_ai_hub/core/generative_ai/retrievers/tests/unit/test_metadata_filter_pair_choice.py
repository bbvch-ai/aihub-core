"""A list value is a choice: the stored value is one of them, or a stored list holds one of them."""

import pytest
from llama_index.core.vector_stores.types import FilterCondition, FilterOperator, MetadataFilters
from llama_index.vector_stores.milvus.utils import parse_standard_filters
from pydantic import ValidationError

from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair


def test_a_list_matches_a_scalar_in_it_or_a_list_holding_one_of_it() -> None:
    llama_filter = MetadataFilterPair(key="lcdm_knowledge_code", value=["NEST/DOK", "KSB/DOK"]).to_llama_index()

    assert isinstance(llama_filter, MetadataFilters)
    assert llama_filter.condition == FilterCondition.OR
    assert [f.operator for f in llama_filter.filters] == [FilterOperator.IN, FilterOperator.ANY]
    assert all(f.value == ["NEST/DOK", "KSB/DOK"] for f in llama_filter.filters)


def test_the_choice_reaches_milvus_as_in_or_array_contains_any() -> None:
    llama_filter = MetadataFilterPair(key="lcdm_knowledge_code", value=["NEST/DOK"]).to_llama_index()

    expression = parse_standard_filters(MetadataFilters(filters=[llama_filter]))[1]

    assert "lcdm_knowledge_code in ['NEST/DOK']" in expression
    assert "array_contains_any(lcdm_knowledge_code, ['NEST/DOK'])" in expression


def test_an_empty_choice_is_refused() -> None:
    with pytest.raises(ValidationError):
        MetadataFilterPair(key="lcdm_knowledge_code", value=[])


def test_a_single_text_still_matches_by_equality_or_contains() -> None:
    llama_filter = MetadataFilterPair(key="department", value="hr").to_llama_index()

    assert isinstance(llama_filter, MetadataFilters)
    assert [f.operator for f in llama_filter.filters] == [FilterOperator.EQ, FilterOperator.CONTAINS]
