from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.utils import get_tokenizer
from llama_index.core.vector_stores.types import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQuery,
    VectorStoreQueryMode,
    VectorStoreQueryResult,
)

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
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
    """The key each filter of the group tests; a nested group counts once, as it tests one key in several ways."""
    return [f.key if isinstance(f, MetadataFilter) else _single_key(f) for f in group.filters]


def _single_key(nested: MetadataFilters) -> str:
    (key,) = {f.key for f in nested.filters}
    return key


def _extra_filter(value: str | int | float | bool) -> MetadataFilter | MetadataFilters:
    store, captured = _capturing_vector_store()
    retrieve_nodes(
        message="q",
        embed_model=_mock_embed_model(),
        retrieve_k=5,
        index_namespaces=["ns1"],
        query_mode=VectorStoreQueryMode.DEFAULT,
        node_types=["content"],
        vector_store=store,
        additional_filters=[MetadataFilterPair(key="labels", value=value)],
    )
    (group,) = _and_groups(captured["filters"])
    return group.filters[-1]


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
            index_namespaces=None,
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

    def test_an_empty_namespace_scope_searches_nothing(self):
        store, captured = _capturing_vector_store()
        nodes = retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=[],
            query_mode=VectorStoreQueryMode.DEFAULT,
            node_types=["content"],
            vector_store=store,
        )
        assert nodes == []
        assert "filters" not in captured

    def test_no_namespace_no_extras_preserves_legacy_flat_or(self):
        store, captured = _capturing_vector_store()
        retrieve_nodes(
            message="q",
            embed_model=_mock_embed_model(),
            retrieve_k=5,
            index_namespaces=None,
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


class TestRetrieveNodesListFilters:
    """#1953: frontmatter stores lists of text, and Milvus never finds a string in a list by equality."""

    def test_a_text_value_matches_an_equal_value_or_a_list_containing_it(self):
        extra = _extra_filter("backend")

        assert isinstance(extra, MetadataFilters)
        assert extra.condition == FilterCondition.OR
        assert [(f.key, f.value, f.operator) for f in extra.filters] == [
            ("labels", "backend", FilterOperator.EQ),
            ("labels", "backend", FilterOperator.CONTAINS),
        ]

    @pytest.mark.parametrize("value", [2, 1.5])
    def test_a_number_keeps_plain_equality(self, value: int | float):
        """Lists hold text only, so a number can only ever equal the stored value."""
        extra = _extra_filter(value)

        assert isinstance(extra, MetadataFilter)
        assert (extra.key, extra.value, extra.operator) == ("labels", value, FilterOperator.EQ)

    @pytest.mark.parametrize(("flag", "text"), [(True, "true"), (False, "false")])
    def test_a_flag_is_compared_as_the_text_ingestion_stores(self, flag: bool, text: str):
        """llama-index's MetadataFilter rejects booleans, so a boolean filter used to fail before reaching Milvus."""
        extra = _extra_filter(flag)

        assert isinstance(extra, MetadataFilters)
        assert [(f.value, f.operator) for f in extra.filters] == [
            (text, FilterOperator.EQ),
            (text, FilterOperator.CONTAINS),
        ]


class TestRetrieveNodesQueryClamp:
    def test_document_sized_message_is_clamped_before_embedding(self):
        """A chat message that inlines an attached document must not reach the embedder past its window."""
        question = "What does the attached contract say about termination?"
        message = ("Contract clause text. " * 6000) + question
        embed = _mock_embed_model()
        embed.model_name = "embedding/bge-m3"
        store, _ = _capturing_vector_store()

        with patch.object(
            EmbeddingModelConfig, "get_model_info", return_value={"model_info": {"max_input_tokens": 8192}}
        ):
            retrieve_nodes(
                message=message,
                embed_model=embed,
                retrieve_k=5,
                index_namespaces=None,
                query_mode=VectorStoreQueryMode.DEFAULT,
                node_types=["content"],
                vector_store=store,
            )

        embedded = embed.get_text_embedding.call_args.args[0]
        assert len(get_tokenizer()(embedded)) <= 4096
        assert embedded.endswith(question)


def _scored_vector_store(scores: list[float]) -> MagicMock:
    store = MagicMock()
    nodes = [TextNode(id_=f"n{index}", text=f"section {index}") for index in range(len(scores))]
    store.query.return_value = VectorStoreQueryResult(nodes=nodes, similarities=scores, ids=[n.id_ for n in nodes])
    return store


def _retrieve(scores: list[float], mode: VectorStoreQueryMode, min_similarity: float | None) -> list[str]:
    nodes = retrieve_nodes(
        message="q",
        embed_model=_mock_embed_model(),
        retrieve_k=5,
        index_namespaces=None,
        query_mode=mode,
        node_types=["content"],
        vector_store=_scored_vector_store(scores),
        min_similarity=min_similarity,
    )
    return [node.node.node_id for node in nodes]


class TestMinimumSimilarity:
    def test_dense_results_below_the_floor_are_dropped(self):
        assert _retrieve([0.71, 0.36, 0.35, 0.34, 0.2], VectorStoreQueryMode.DEFAULT, 0.35) == ["n0", "n1", "n2"]

    def test_nothing_above_the_floor_returns_no_nodes(self):
        assert _retrieve([0.31, 0.28], VectorStoreQueryMode.DEFAULT, 0.35) == []

    def test_no_floor_or_zero_keeps_every_result(self):
        assert _retrieve([0.71, 0.1], VectorStoreQueryMode.DEFAULT, None) == ["n0", "n1"]
        assert _retrieve([0.71, 0.1], VectorStoreQueryMode.DEFAULT, 0.0) == ["n0", "n1"]

    def test_hybrid_scores_are_not_cosine_and_are_never_cut(self):
        """Hybrid scores are min-max normalised per query, so its weakest result always scores 0."""
        assert _retrieve([0.03, 0.02, 0.01], VectorStoreQueryMode.HYBRID, 0.35) == ["n0", "n1", "n2"]

    def test_sparse_scores_are_not_cosine_and_are_never_cut(self):
        assert _retrieve([0.2, 0.1], VectorStoreQueryMode.SPARSE, 0.35) == ["n0", "n1"]
