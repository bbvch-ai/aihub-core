from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle


class MinMaxScoreNormalizer(BaseNodePostprocessor):
    """
    Normalizes node scores to [0, 1] range using min-max normalization within the result set.

    Unlike ScoreScalerPostProcessor which uses fixed bounds, this normalizer dynamically
    computes bounds from the actual scores. Use this when the score range is unknown or
    varies based on data distribution (e.g., Milvus hybrid search with WeightedRanker).
    """

    floor: float = 0.5
    """Minimum score for the worst result. Prevents low scores when results are similar."""

    @classmethod
    def class_name(cls) -> str:
        return "MinMaxScoreNormalizer"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        if not nodes:
            return nodes

        scores = [node.score for node in nodes if node.score is not None]
        if not scores:
            return nodes

        min_score = min(scores)
        max_score = max(scores)

        # All scores identical: assign maximum relevance
        if max_score == min_score:
            for node in nodes:
                if node.score is not None:
                    node.score = 1.0
            return nodes

        # Normalize to [floor, 1.0] range
        for node in nodes:
            if node.score is not None:
                normalized = (node.score - min_score) / (max_score - min_score)
                node.score = self.floor + normalized * (1.0 - self.floor)

        return nodes
