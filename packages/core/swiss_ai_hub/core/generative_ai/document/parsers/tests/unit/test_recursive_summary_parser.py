import json
import logging
from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.llms.openai_like import OpenAILike

from swiss_ai_hub.core.generative_ai.document.parsers.recursive_summary_parser import (
    SUMMARIZATION_BUDGET_SAFETY_FACTOR,
    LLMSummarizer,
    RecursiveNodeSummarizer,
)
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import HEADING_LEVEL, INDEX, NODE_TYPE_SUMMARY, TYPE


@pytest.fixture
def mock_llm():
    return MagicMock(spec=OpenAILike)


def _recording_predict(prompts: list[str]):
    """A `predict` side effect that records the exact rendered prompt each call sent."""

    def predict(template, text):
        prompts.append(template.format(text=text))
        return "s"

    return predict


def _one_token_per_char(text: str) -> list[int]:
    """A token counter with a 1:1 char-to-token ratio, so budget arithmetic in assertions is exact."""
    return [0] * len(text)


def test_nodes_with_next_relationship(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    node1 = TextNode(
        text="Node 1 text",
        metadata={"h1": "Header 1"},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node2")},
    )
    node2 = TextNode(
        id_="node2",
        text="Node 2 text",
        metadata={"h1": "Header 1"},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node3")},
    )
    node3 = TextNode(
        id_="node3",
        text="Node 3 text",
        metadata={"h1": "Header 1"},
        relationships={},
    )
    nodes = [node1, node2, node3]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) == 2


def test_no_level_zero_node(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    node1 = TextNode(text="Node 1 text", metadata={"h2": "Header 2"}, relationships={})
    node2 = TextNode(text="Node 2 text", metadata={"h2": "Header 2"}, relationships={})
    nodes = [node1, node2]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) > 0


def test_hierarchical_nodes(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    node1 = TextNode(text="Introduction text", metadata={"h1": "Introduction"}, relationships={})
    node2 = TextNode(
        text="Section 1 text",
        metadata={"h1": "Introduction", "h2": "Section 1"},
        relationships={},
    )
    node3 = TextNode(
        text="Subsection 1.1 text",
        metadata={"h1": "Introduction", "h2": "Section 1", "h3": "Subsection 1.1"},
        relationships={},
    )
    nodes = [node1, node2, node3]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) == 4
    for summary_node in summaries:
        child_nodes = [
            node
            for node in summarized_nodes
            if node.relationships.get(NodeRelationship.PARENT, None) == RelatedNodeInfo(node_id=summary_node.node_id)
        ]
        assert len(child_nodes) > 0


def test_text_under_min_summarization_length(mock_llm):
    short_text = "i" * 100
    mock_llm.predict.return_value = "This is a mock summary."
    node = TextNode(text=short_text, metadata={"h1": "Long Text"}, relationships={})
    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, min_summarization_length=200)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summary_nodes = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summary_nodes) == 2
    assert summary_nodes[0].text == short_text
    assert summary_nodes[1].text == "This is a mock summary."


def test_recursive_splitting_and_summarization(mock_llm):
    mock_llm.predict.return_value = "Summarized recursive text"
    very_long_text = "sentence. " * 5000
    node = TextNode(text=very_long_text, metadata={"h1": "Very Long Text"}, relationships={})
    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) > 0
    assert len(summaries[0].text) < len(very_long_text)


def test_parent_child_relationships(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    parent = TextNode(text="Parent text", metadata={"h1": "Parent"}, relationships={})
    child = TextNode(text="Child text", metadata={"h1": "Parent", "h2": "Child"}, relationships={})

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes([parent, child])
    summary_nodes = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    parent_summary = next((n for n in summary_nodes if n.metadata.get(HEADING_LEVEL) == 1), None)
    child_summary = next((n for n in summary_nodes if n.metadata.get(HEADING_LEVEL) == 2), None)

    assert parent_summary is not None
    assert child_summary is not None
    assert NodeRelationship.PARENT in child_summary.relationships
    assert child_summary.relationships[NodeRelationship.PARENT].node_id == parent_summary.node_id
    assert NodeRelationship.CHILD in parent_summary.relationships
    assert any(child.node_id == child_summary.node_id for child in parent_summary.relationships[NodeRelationship.CHILD])


def test_multiple_child_nodes(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    node1 = TextNode(
        id_="node1",
        text="Child 1 text",
        metadata={"h1": "Parent"},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node2")},
    )
    node2 = TextNode(
        id_="node2",
        text="Child 2 text",
        metadata={"h1": "Parent"},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node3")},
    )
    node3 = TextNode(id_="node3", text="Child 3 text", metadata={"h1": "Parent"}, relationships={})
    nodes = [node1, node2, node3]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) == 2
    assert len(summaries[0].relationships[NodeRelationship.CHILD]) == 3
    assert RelatedNodeInfo(node_id=node1.node_id) in summaries[0].relationships[NodeRelationship.CHILD]
    assert RelatedNodeInfo(node_id=node2.node_id) in summaries[0].relationships[NodeRelationship.CHILD]
    assert RelatedNodeInfo(node_id=node3.node_id) in summaries[0].relationships[NodeRelationship.CHILD]


def test_no_nodes(mock_llm):
    nodes: list[TextNode] = []

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    assert len(summarized_nodes) == 0


def test_single_node_summarization(mock_llm):
    mock_llm.predict.return_value = "Summarized single node text"
    node = TextNode(text="This is a test node.", metadata={"h1": "Test Header"}, relationships={})
    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, min_summarization_length=0)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) == 2
    expected_summary = "Summarized single node text"
    assert summaries[0].text == expected_summary


def test_nodes_with_missing_headers(mock_llm):
    mock_llm.predict.return_value = "Summarized text without headers"
    node1 = TextNode(
        text="Node 1 text without header",
        metadata={},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node2")},
    )
    node2 = TextNode(id_="node2", text="Node 2 text without header", metadata={}, relationships={})
    nodes = [node1, node2]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [node for node in summarized_nodes if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summaries) == 1


def test_basic_summarization(mock_llm):
    mock_llm.predict.return_value = "Summarized text"

    node = TextNode(
        text="This is some content to summarize. " * 50,
        metadata={"h1": "Test Header"},
        relationships={},
    )

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes([node])

    summary_nodes = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]

    assert len(summary_nodes) == 2
    level1_summary = next((n for n in summary_nodes if n.metadata.get(HEADING_LEVEL) == 1), None)
    assert level1_summary is not None
    assert level1_summary.text == "Summarized text"
    assert level1_summary.metadata.get("h1") == "Test Header"
    assert level1_summary.metadata.get(INDEX) == 0


def test_short_text_not_summarized(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    short_text = "This is short content."
    node = TextNode(
        text=short_text,
        metadata={"h1": "Short Header"},
        relationships={},
    )

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, min_summarization_length=100)
    summarized_nodes = summarizer.summarize_nodes([node])
    summary_nodes = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    level1_summary = next((n for n in summary_nodes if n.metadata.get(HEADING_LEVEL) == 1), None)

    assert level1_summary is not None
    assert level1_summary.text == short_text
    assert mock_llm.predict.call_count < 2


def test_sequential_indices(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    node1 = TextNode(text="First section", metadata={"h1": "First"}, relationships={})
    node2 = TextNode(text="Second section", metadata={"h1": "Second"}, relationships={})

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes([node1, node2])
    summary_nodes = [
        n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY and n.metadata.get(HEADING_LEVEL) == 1
    ]
    summary_nodes.sort(key=lambda x: x.metadata.get("h1", ""))

    assert len(summary_nodes) == 2
    assert summary_nodes[0].metadata.get(INDEX) == 0
    assert summary_nodes[1].metadata.get(INDEX) == 1


def test_flat_headerless_root_map_reduces_within_budget(mock_llm):
    """Reproduces issue #158: a headerless root fans in every h1-only sibling as its child."""
    prompts: list[str] = []
    mock_llm.predict.side_effect = _recording_predict(prompts)

    siblings = [TextNode(text="short section text", metadata={"h1": f"Section {i}"}) for i in range(2500)]
    headerless_root = TextNode(text="", metadata={})
    nodes = [headerless_root, *siblings]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, max_input_tokens=4000, token_counter=_one_token_per_char)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    budget = int(4000 * SUMMARIZATION_BUDGET_SAFETY_FACTOR)
    assert prompts
    assert all(len(p) <= budget for p in prompts)
    assert mock_llm.predict.call_count > 1

    summaries = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    assert len(summaries) == len(siblings) + 1


def test_all_headerless_document_map_reduces_within_budget(mock_llm):
    """A chain of headerless nodes merges into one group via the NEXT-relationship walk, not fan-in."""
    prompts: list[str] = []
    mock_llm.predict.side_effect = _recording_predict(prompts)

    nodes = [TextNode(id_=f"n{i}", text="chunk of body text. " * 3, metadata={}) for i in range(2000)]
    for previous_node, current_node in zip(nodes, nodes[1:]):
        previous_node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=current_node.node_id)

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, max_input_tokens=4000, token_counter=_one_token_per_char)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    budget = int(4000 * SUMMARIZATION_BUDGET_SAFETY_FACTOR)
    assert prompts
    assert all(len(p) <= budget for p in prompts)

    summaries = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    assert len(summaries) == 1


def test_parent_with_many_children_map_reduces_within_budget(mock_llm):
    """Proves map-reduce actually ran, which `test_recursive_splitting_and_summarization` only claims by name."""
    prompts: list[str] = []
    mock_llm.predict.side_effect = _recording_predict(prompts)

    parent = TextNode(text="Parent overview", metadata={"h1": "Parent"})
    children = [
        TextNode(text="child body text " * 5, metadata={"h1": "Parent", "h2": f"Child {i}"}) for i in range(600)
    ]
    nodes = [parent, *children]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, max_input_tokens=3000, token_counter=_one_token_per_char)
    summarizer.summarize_nodes(nodes)

    budget = int(3000 * SUMMARIZATION_BUDGET_SAFETY_FACTOR)
    assert prompts
    assert all(len(p) <= budget for p in prompts)
    assert mock_llm.predict.call_count > 1


def test_unreducible_summary_is_skipped_and_logged(mock_llm, caplog):
    """A budget smaller than the prompt template's own fixed overhead can never be satisfied by any input."""
    node = TextNode(text="This section cannot ever be reduced to fit.", metadata={"h1": "Stuck Section"})

    summarizer = RecursiveNodeSummarizer(
        llm=mock_llm, min_summarization_length=0, max_input_tokens=1, token_counter=_one_token_per_char
    )

    with caplog.at_level(logging.WARNING):
        summarized_nodes = summarizer.summarize_nodes([node])

    summaries = [n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY]
    assert summaries == []
    assert "Stuck Section" in caplog.text
    mock_llm.predict.assert_not_called()


def test_token_counter_transport_failure_propagates_instead_of_being_swallowed(mock_llm):
    """
    A malformed response from the token-counter or LLM gateway (e.g. a 413/502 HTML error page) must not be
    mistaken for the deliberate "this section can't be reduced" signal and silently dropped.
    """

    def raising_token_counter(text: str) -> list[int]:
        raise json.JSONDecodeError("Expecting value", "<html>502 Bad Gateway</html>", 0)

    node = TextNode(text="x" * 2000, metadata={"h1": "Section"})

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, max_input_tokens=4000, token_counter=raising_token_counter)

    with pytest.raises(json.JSONDecodeError):
        summarizer.summarize_nodes([node])


def test_fits_short_circuits_without_touching_the_token_counter():
    """The char-count thresholds in `_fits` are load-bearing: they keep oversized payloads off the network."""
    calls: list[str] = []

    def counting_token_counter(text: str) -> list[int]:
        calls.append(text)
        return [0] * len(text)

    summarizer = LLMSummarizer(
        llm=MagicMock(spec=OpenAILike),
        t=LocaleHandler(locale="en"),
        max_input_tokens=4000,
        token_counter=counting_token_counter,
    )
    budget = summarizer._budget
    calls.clear()  # __init__ already measured the template overhead once

    assert summarizer._fits("s" * 10) is True
    assert summarizer._fits("s" * (budget * 5)) is False
    assert calls == []


def test_sibling_relationships(mock_llm):
    mock_llm.predict.return_value = "Summarized text"
    parent = TextNode(text="Parent section", metadata={"h1": "Parent"}, relationships={})
    child1 = TextNode(text="First child", metadata={"h1": "Parent", "h2": "Child1"}, relationships={})
    child2 = TextNode(text="Second child", metadata={"h1": "Parent", "h2": "Child2"}, relationships={})

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes([parent, child1, child2])
    summary_nodes = [
        n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY and n.metadata.get(HEADING_LEVEL) == 2
    ]
    summary_nodes.sort(key=lambda x: x.metadata.get("h2", ""))

    assert len(summary_nodes) == 2
    child1_summary = summary_nodes[0]
    child2_summary = summary_nodes[1]
    assert NodeRelationship.NEXT in child1_summary.relationships
    assert child1_summary.relationships[NodeRelationship.NEXT].node_id == child2_summary.node_id
    assert NodeRelationship.PREVIOUS in child2_summary.relationships
    assert child2_summary.relationships[NodeRelationship.PREVIOUS].node_id == child1_summary.node_id
