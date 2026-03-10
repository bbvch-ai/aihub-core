from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle


class ScoreScalerPostProcessor(BaseNodePostprocessor):
    from_min: int
    from_max: int

    to_min: int = 0
    to_max: int = 1

    @classmethod
    def class_name(cls) -> str:
        return "ScoreScalerPostProcessor"

    def _postprocess_nodes(
        self,
        nodes: list[NodeWithScore],
        query_bundle: QueryBundle | None = None,
    ) -> list[NodeWithScore]:
        for node in nodes:
            node.score = self._scale_score(node.score)
        return nodes

    def _scale_score(self, score: float) -> float:
        return self.to_min + (score - self.from_min) * (self.to_max - self.to_min) / (self.from_max - self.from_min)
