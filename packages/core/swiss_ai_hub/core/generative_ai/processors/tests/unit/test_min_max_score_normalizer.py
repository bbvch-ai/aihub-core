from llama_index.core.schema import NodeWithScore, TextNode

from swiss_ai_hub.core.generative_ai.processors.min_max_score_normalizer import MinMaxScoreNormalizer

import pytest
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401

class TestMinMaxScoreNormalizer:
    def test_normalizes_scores_to_range(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="best"), score=0.8),
            NodeWithScore(node=TextNode(text="middle"), score=0.5),
            NodeWithScore(node=TextNode(text="worst"), score=0.2),
        ]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        assert result[0].score == 1.0
        assert result[2].score == 0.5
        assert 0.5 < result[1].score < 1.0

    def test_handles_identical_scores(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="a"), score=0.5),
            NodeWithScore(node=TextNode(text="b"), score=0.5),
        ]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        for node in result:
            assert node.score == 1.0

    def test_handles_empty_list(self) -> None:
        assert MinMaxScoreNormalizer().postprocess_nodes([]) == []

    def test_handles_single_node(self) -> None:
        nodes = [NodeWithScore(node=TextNode(text="only"), score=0.3)]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        assert result[0].score == 1.0

    def test_handles_none_scores(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="has_score"), score=0.8),
            NodeWithScore(node=TextNode(text="no_score"), score=None),
            NodeWithScore(node=TextNode(text="another"), score=0.4),
        ]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        assert result[0].score == 1.0
        assert result[1].score is None
        assert result[2].score == 0.5

    def test_custom_floor(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="best"), score=1.0),
            NodeWithScore(node=TextNode(text="worst"), score=0.0),
        ]

        result = MinMaxScoreNormalizer(floor=0.3).postprocess_nodes(nodes)

        assert result[0].score == 1.0
        assert result[1].score == 0.3

    def test_preserves_node_order(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="first", id_="1"), score=0.1),
            NodeWithScore(node=TextNode(text="second", id_="2"), score=0.9),
        ]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        assert result[0].node.id_ == "1"
        assert result[1].node.id_ == "2"

    def test_handles_very_small_score_differences(self) -> None:
        nodes = [
            NodeWithScore(node=TextNode(text="a"), score=0.032),
            NodeWithScore(node=TextNode(text="b"), score=0.0),
        ]

        result = MinMaxScoreNormalizer().postprocess_nodes(nodes)

        assert result[0].score == 1.0
        assert result[1].score == 0.5
