from typing import Any
from unittest.mock import MagicMock

from llama_index.core.vector_stores.types import (
    FilterCondition,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)

from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, TYPE


def _mock_embed_model() -> MagicMock:
    embed = MagicMock()
    embed.get_text_embedding.return_value = [0.1, 0.2, 0.3]
    return embed


def _capturing_vector_store() -> tuple[MagicMock, dict[str, Any]]:
    captured: dict[str, Any] = {}
    store = MagicMock()

    def _query(query: VectorStoreQuery) -> VectorStoreQueryResult:
        captured["filters"] = query.filters
        return VectorStoreQueryResult(nodes=[], similarities=[], ids=[])

    store.query.side_effect = _query
    return store, captured


def _and_groups(filters: MetadataFilters) -> list[MetadataFilters]:
    assert filters.condition == FilterCondition.OR
    return [inner for inner in filters.filters if isinstance(inner, MetadataFilters)]


def _keys(group: MetadataFilters) -> list[str]:
    return [f.key for f in group.filters if isinstance(f, MetadataFilter)]


class TestRetrieveNodesFilters:
    def test_namespace_branch_includes_extras_in_each_and_group(self):
        store, captured = _capturing_vector_store()
        retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=["ns1", "ns2"],
            query_mode=VectorStoreQueryMode.DEFAULT,
            node_types=["content"],
            vector_store=store,
            additional_filters=[MetadataFilterPair(key="snk", value="12345")],
        )
        groups = _and_groups(captured["filters"])
        assert len(groups) == 2
        for group in groups:
            assert group.condition == FilterCondition.AND
            assert _keys(group) == [NAMESPACE, TYPE, "snk"]

    def test_no_namespace_branch_with_extras_wraps_in_and_groups(self):
        store, captured = _capturing_vector_store()
        retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=[],
            query_mode=VectorStoreQueryMode.DEFAULT,
            node_types=["content", "summary"],
            vector_store=store,
            additional_filters=[MetadataFilterPair(key="snk", value="12345")],
        )
        groups = _and_groups(captured["filters"])
        assert len(groups) == 2
        for group in groups:
            assert group.condition == FilterCondition.AND
            assert _keys(group) == [TYPE, "snk"]

    def test_no_namespace_no_extras_preserves_legacy_flat_or(self):
        store, captured = _capturing_vector_store()
        retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=[],
            query_mode=VectorStoreQueryMode.DEFAULT,
            node_types=["content", "summary"],
            vector_store=store,
        )
        filters = captured["filters"]
        assert filters.condition == FilterCondition.OR
        # flat list of MetadataFilter (no nested AND groups) for backwards compatibility
        assert all(isinstance(f, MetadataFilter) for f in filters.filters)
        assert [f.key for f in filters.filters] == [TYPE, TYPE]

    def test_namespace_branch_without_extras_matches_legacy_structure(self):
        store, captured = _capturing_vector_store()
        retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=["ns1"],
            query_mode=VectorStoreQueryMode.DEFAULT,
            node_types=["content"],
            vector_store=store,
        )
        groups = _and_groups(captured["filters"])
        assert len(groups) == 1
        assert _keys(groups[0]) == [NAMESPACE, TYPE]
