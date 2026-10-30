"""The exact budgets against the real models behind LiteLLM: the largest nodes the parser emits embed, and a rerank
with a long query and a node as large as the old ceiling allowed is not refused. Three upstream calls in all; the
model_info is given here, so the running LiteLLM does not need the new config keys."""

from typing import Any

import pytest
from llama_index.core.schema import Document, MetadataMode

from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    MarkdownStructuralNodeParser,
)
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.rerank.rerank_nodes import rerank_nodes
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE, NODE_CONTENT_TYPE_TEXT, SOURCE

EMBEDDING_MODEL = "embedding/bge-m3"
RERANKING_MODEL = "reranker/bge"
WINDOW = 8192


def _declared(config_class: type, mode: str, overhead: int, monkeypatch: pytest.MonkeyPatch) -> None:
    """Adds the tokenizer keys to the model's real LiteLLM entry, whatever config the running LiteLLM loaded."""
    fetch = config_class.get_model_info

    def with_tokenizer(self: Any) -> dict[str, Any]:
        entry = fetch(self)
        return {
            **entry,
            "model_info": {
                **entry["model_info"],
                "mode": mode,
                "max_input_tokens": WINDOW,
                "aihub_tokenizer": "bge-m3",
                "aihub_input_overhead_tokens": overhead,
            },
        }

    monkeypatch.setattr(config_class, "get_model_info", with_tokenizer)


def _code_listing() -> str:
    line = (
        "    totals[region] = sum(order.amount * (1 - order.discount) for order in orders if order.region == region)\n"
    )
    return "def regional_totals(orders, regions):\n    totals = {}\n" + line * 400


def test_the_largest_parsed_nodes_embed_without_exceeding_the_window(monkeypatch: pytest.MonkeyPatch) -> None:
    _declared(EmbeddingModelConfig, "embedding", 2, monkeypatch)
    digits = " ".join(str(number * 7919) for number in range(6000))
    text = f"# Listing\n<figure>{_code_listing()}</figure>\n# Figures\n<table>{digits}</table>"
    parser = MarkdownStructuralNodeParser(metadata={SOURCE: "budget-check.md"}, embedding_model_name=EMBEDDING_MODEL)

    nodes = parser.get_nodes_from_node(Document(text=text))
    largest = [
        max(
            (node for node in nodes if node.metadata.get(NODE_CONTENT_TYPE) == content_type),
            key=lambda node: len(node.get_content(metadata_mode=MetadataMode.EMBED)),
        )
        for content_type in ("figure", "table")
    ]
    embed_model, _ = EmbeddingModelConfig(model_name=EMBEDDING_MODEL).to_llama_index()

    embeddings = embed_model.get_text_embedding_batch(
        [node.get_content(metadata_mode=MetadataMode.EMBED) for node in largest]
    )

    assert len(embeddings) == 2
    assert all(len(embedding) == 1024 for embedding in embeddings)


@pytest.mark.asyncio
async def test_rerank_with_a_long_query_and_a_legacy_sized_node_is_not_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    _declared(RerankingModelConfig, "rerank", 4, monkeypatch)
    tokenizer = ModelTokenizer.shared("bge-m3")
    legacy = "def regional_totals(orders, regions):\n"
    while tokenizer.count(legacy) < 8200:
        legacy += "    totals[region] = sum(order.amount for order in orders if order.region == region)\n"
    nodes = [
        IngestedNode(
            id=node_id,
            content=content,
            content_type=NODE_CONTENT_TYPE_TEXT,
            document_id="budget-check",
            source="budget-check.md",
            namespace="budget",
            created_at="2026-10-30T00:00:00Z",
            updated_at="2026-10-30T00:00:00Z",
            inserted_at="2026-10-30T00:00:00Z",
            metadata={},
        )
        for node_id, content in (("legacy", legacy), ("notice", "Termination requires 30 days written notice."))
    ]
    query = ("Clause text from the attached contract. " * 1500) + "What is the notice period?"

    reranked = await rerank_nodes(nodes, query, RerankingModelConfig(model_name=RERANKING_MODEL, top_n=2))

    assert {node.id for node in reranked} == {"legacy", "notice"}
    assert next(node for node in reranked if node.id == "legacy").content == legacy
