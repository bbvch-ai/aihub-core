"""Tests for embed_nodes degrading on rejected chunks instead of failing the whole document."""

from unittest.mock import patch

import httpx
import pytest
from dagster import build_op_context
from llama_index.core.schema import TextNode
from openai import BadRequestError, InternalServerError
from pydantic import BaseModel
from pydantic_core import ValidationError

from swiss_ai_hub.pipeline.ops.nodes.embed_nodes import embed_nodes


def make_nodes(count: int) -> list[TextNode]:
    return [TextNode(text=f"content {i}", id_=f"node-{i}") for i in range(count)]


def context_length_error() -> BadRequestError:
    """The 400 the model actually returns — an openai error, never a pydantic ValidationError."""
    response = httpx.Response(
        status_code=400, request=httpx.Request("POST", "http://litellm/v1/embeddings"), text="context length"
    )
    return BadRequestError(
        "This model's maximum context length is 8192 tokens. However, you requested 17555 tokens",
        response=response,
        body=None,
    )


def validation_error() -> ValidationError:
    """The error this op caught before BadRequestError was identified, and which is still handled."""

    class Probe(BaseModel):
        value: int

    try:
        Probe(value="not-an-int")
    except ValidationError as error:
        return error
    raise AssertionError("Probe was expected to reject a non-integer")


class FakeEmbeddingModel:
    """Rejects any text whose node id appears in `reject`, mirroring a per-input deterministic 400."""

    def __init__(self, reject: set[str] | None = None, error: Exception | None = None) -> None:
        self.reject = reject or set()
        self.error = error or context_length_error()
        self.batch_calls = 0

    def get_text_embedding_batch(self, texts: list[str]) -> list[list[float]]:
        self.batch_calls += 1
        if any(self._rejected(text) for text in texts):
            raise self.error
        return [[0.1, 0.2, 0.3] for _ in texts]

    def _rejected(self, text: str) -> bool:
        return any(f"content {node_id.removeprefix('node-')}" == text for node_id in self.reject)


_MODULE = "swiss_ai_hub.pipeline.ops.nodes.embed_nodes"


def run_embed_nodes(nodes: list[TextNode], model: FakeEmbeddingModel):
    """The op resolves the embedding model from the run's knowledge database, so the fake is patched in
    where that lookup happens rather than injected as a resource."""
    with patch(f"{_MODULE}.build_embedding_model", return_value=model):
        return embed_nodes(build_op_context(partition_key="bucket|s3:%2F%2Fbucket%2Fa.pdf"), nodes)


class TestEmbedNodes:
    def test_all_nodes_embed_when_the_model_accepts_them(self) -> None:
        nodes = make_nodes(4)

        result = run_embed_nodes(nodes, FakeEmbeddingModel())

        assert len(result.value) == 4
        assert all(node.embedding == [0.1, 0.2, 0.3] for node in result.value)

    def test_single_rejected_node_does_not_fail_the_document(self) -> None:
        """The bug: one oversized table node failed the partition and cost the document its other 44 nodes."""
        nodes = make_nodes(8)

        result = run_embed_nodes(nodes, FakeEmbeddingModel(reject={"node-3"}))

        assert len(result.value) == 7
        assert "node-3" not in {node.node_id for node in result.value}

    def test_rejected_node_is_reported_in_metadata(self) -> None:
        nodes = make_nodes(8)

        result = run_embed_nodes(nodes, FakeEmbeddingModel(reject={"node-3"}))

        assert result.metadata["Number of Embedded Nodes"].value == 7
        assert result.metadata["Number of Skipped Nodes"].value == 1

    def test_batch_rejection_bisects_to_isolate_the_bad_node(self) -> None:
        nodes = make_nodes(8)
        model = FakeEmbeddingModel(reject={"node-5"})

        result = run_embed_nodes(nodes, model)

        assert len(result.value) == 7
        # 1 failed whole batch, then a bisect down to the single offender rather than dropping the batch.
        assert model.batch_calls > 1

    def test_multiple_rejected_nodes_are_all_skipped(self) -> None:
        nodes = make_nodes(8)

        result = run_embed_nodes(nodes, FakeEmbeddingModel(reject={"node-0", "node-7"}))

        assert {node.node_id for node in result.value} == {f"node-{i}" for i in range(1, 7)}

    def test_every_node_rejected_fails_the_op_instead_of_reporting_an_empty_success(self) -> None:
        """
        A total refusal is a misconfiguration, not oversized content.

        An empty success would stamp an unchanged DataVersion downstream and leave the document unindexed behind
        a green asset, with nothing to trigger a retry - strictly worse than failing the partition.
        """
        nodes = make_nodes(2)

        with pytest.raises(RuntimeError, match="rejected all 2 nodes"):
            run_embed_nodes(nodes, FakeEmbeddingModel(reject={"node-0", "node-1"}))

    def test_no_nodes_is_not_treated_as_a_total_rejection(self) -> None:
        result = run_embed_nodes([], FakeEmbeddingModel(reject=set()))

        assert result.value == []

    def test_validation_errors_are_bisected_and_skipped_like_bad_requests(self) -> None:
        nodes = make_nodes(4)

        result = run_embed_nodes(nodes, FakeEmbeddingModel(reject={"node-2"}, error=validation_error()))

        assert {node.node_id for node in result.value} == {"node-0", "node-1", "node-3"}
        assert result.metadata["Number of Skipped Nodes"].value == 1

    def test_transient_errors_still_propagate_so_dagster_retries_them(self) -> None:
        response = httpx.Response(
            status_code=500, request=httpx.Request("POST", "http://litellm/v1/embeddings"), text="boom"
        )
        model = FakeEmbeddingModel(
            reject={"node-0"}, error=InternalServerError("upstream down", response=response, body=None)
        )

        with pytest.raises(InternalServerError):
            run_embed_nodes(make_nodes(2), model)
