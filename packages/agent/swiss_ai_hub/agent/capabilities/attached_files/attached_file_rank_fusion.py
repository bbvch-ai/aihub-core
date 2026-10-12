from swiss_ai_hub.core.generative_ai import IngestedNode

RRF_K = 60


class AttachedFileRankFusion:
    """Merges the lexical and the dense ranking of a file's sections into one order.

    Reciprocal rank fusion needs no score calibration between BM25 and cosine, and its `k` of 60 is the convention
    the knowledge search's Milvus `RRFRanker` uses too. Sections are keyed by `index`, because node ids are drawn anew
    on every parse.
    """

    @staticmethod
    def fuse(rankings: list[list[IngestedNode]], k: int = RRF_K) -> list[IngestedNode]:
        scores: dict[int, float] = {}
        sections: dict[int, IngestedNode] = {}
        for ranking in rankings:
            for rank, section in enumerate(ranking, start=1):
                key = section.index or 0
                scores[key] = scores.get(key, 0.0) + 1 / (k + rank)
                sections.setdefault(key, section)
        return [sections[key] for key in sorted(scores, key=lambda key: scores[key], reverse=True)]
