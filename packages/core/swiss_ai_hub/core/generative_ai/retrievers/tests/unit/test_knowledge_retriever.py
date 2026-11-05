"""The minimum similarity drops weak dense results before their neighbours and summaries are fetched, so the nodes
added for the results kept, which carry no score of their own, are never cut by it."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.generative_ai.processors.models.retrieve_prev_next_config import RetrievePrevNextConfig
from swiss_ai_hub.core.generative_ai.processors.models.retrieve_summaries_config import RetrieveSummariesConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever import KnowledgeRetriever
from swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever_config import KnowledgeRetrieverConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig

RETRIEVER_MODULE = "swiss_ai_hub.core.generative_ai.retrievers.knowledge_retriever"
METADATA = {"source": "handbook.pdf", "namespace": "hr", "document_id": "doc-1"}


def _config(**overrides) -> KnowledgeRetrieverConfig:
    return KnowledgeRetrieverConfig(
        embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"),
        vector_store=MilvusVectorStoreConfig(collection_name="handbooks", index_namespaces=["hr"]),
        **overrides,
    )


def _store(scores: list[float]) -> MagicMock:
    store = MagicMock()
    nodes = [TextNode(id_=f"hit{index}", text=f"section {index}", metadata=METADATA) for index in range(len(scores))]
    store.query.return_value = VectorStoreQueryResult(nodes=nodes, similarities=scores, ids=[n.id_ for n in nodes])
    return store


def _with_unscored_additions(prefix: str, score: float | None):
    """Stands in for the neighbour and summary fetches, recording which results they were asked to expand."""
    expanded: list[str] = []

    def expand(nodes: list[NodeWithScore], **_kwargs) -> list[NodeWithScore]:
        expanded.extend(node.node.node_id for node in nodes)
        added = [
            NodeWithScore(
                node=TextNode(id_=f"{prefix}-{node.node.node_id}", text="near", metadata=METADATA), score=score
            )
            for node in nodes
        ]
        return [*nodes, *added]

    return expand, expanded


@pytest.mark.asyncio
async def test_neighbours_and_summaries_come_only_for_the_results_kept():
    config = _config(
        retrieve_prev_next=RetrievePrevNextConfig(num_nodes=1), retrieve_summaries=RetrieveSummariesConfig()
    )
    embed = MagicMock()
    embed.get_text_embedding.return_value = [1.0, 0.0]
    neighbours, asked_for_neighbours = _with_unscored_additions("neighbour", None)
    summaries, asked_for_summaries = _with_unscored_additions("summary", 0.0)

    with (
        patch.object(EmbeddingModelConfig, "to_llama_index", return_value=(embed, None)),
        patch.object(MilvusVectorStoreConfig, "to_llama_index", return_value=_store([0.62, 0.41, 0.3])),
        patch(f"{RETRIEVER_MODULE}.retrieve_prev_next_nodes", side_effect=neighbours),
        patch(f"{RETRIEVER_MODULE}.retrieve_parent_summary_nodes", side_effect=summaries),
    ):
        found = await KnowledgeRetriever(config).retrieve("parental leave", LocaleHandler("en"))

    assert asked_for_neighbours == ["hit0", "hit1"]
    assert "hit2" not in {node.id for node in found}
    assert {"neighbour-hit0", "neighbour-hit1", "summary-hit0", "summary-neighbour-hit0"} <= {node.id for node in found}
    assert "hit2" not in asked_for_summaries


def test_a_stored_retriever_without_the_field_gets_the_default_floor():
    stored = _config().model_dump(exclude={"min_similarity"})

    assert KnowledgeRetrieverConfig.model_validate(stored).min_similarity == 0.35


@pytest.mark.parametrize("value", [-0.1, 1.1])
def test_the_floor_is_a_similarity_between_zero_and_one(value: float):
    with pytest.raises(ValueError):
        _config(min_similarity=value)


def test_admins_can_set_the_floor_in_the_retriever_form():
    names = {element.name for element in KnowledgeRetrieverConfig.as_form().to_formkit_form()}

    assert "min_similarity" in names
