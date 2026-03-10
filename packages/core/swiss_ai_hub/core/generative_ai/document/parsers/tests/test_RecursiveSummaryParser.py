from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.llms.openai_like import OpenAILike

from swiss_ai_hub.core.generative_ai.document.parsers.RecursiveSummaryParser import RecursiveNodeSummarizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import HEADING_LEVEL, INDEX, NODE_TYPE_SUMMARY, TYPE


@pytest.fixture
def mock_llm():
    return MagicMock(spec=OpenAILike)


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
