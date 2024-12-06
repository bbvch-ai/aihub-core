from typing import List
from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.llms.azure_openai import AzureOpenAI

from lib_core.persistence.rag.vectors.node_metadata import HEADING_LEVEL, NODE_TYPE_SUMMARY, TYPE
from lib_core.generative_ai.document.parsers.RecursiveSummaryParser import RecursiveNodeSummarizer


@pytest.fixture
def mock_llm():
    return MagicMock(spec=AzureOpenAI)


def test_nodes_with_next_relationship(mock_llm):
    # Set up the mock LLM to return a fixed summary
    mock_llm.predict.return_value = "Summarized text"

    # Create nodes with NEXT relationships
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

    # Check that summaries are created
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 2  # One for each level


def test_no_level_zero_node(mock_llm):
    mock_llm.predict.return_value = "Summarized text"

    # Create nodes without any level 0 headers
    node1 = TextNode(text="Node 1 text", metadata={"h2": "Header 2"}, relationships={})
    node2 = TextNode(text="Node 2 text", metadata={"h2": "Header 2"}, relationships={})

    nodes = [node1, node2]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Check that summaries are created even without level 0 nodes
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) > 0


def test_hierarchical_nodes(mock_llm):
    mock_llm.predict.return_value = "Summarized text"

    # Create a hierarchy of nodes with different header levels
    node1 = TextNode(
        text="Introduction text", metadata={"h1": "Introduction"}, relationships={}
    )
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

    # Check that summaries are created for each level
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 4  # One summary per level and overall

    # Verify parent-child relationships
    for summary_node in summaries:
        child_nodes = [
            node
            for node in summarized_nodes
            if node.relationships.get(NodeRelationship.PARENT, None)
            == RelatedNodeInfo(node_id=summary_node.node_id)
        ]
        assert len(child_nodes) > 0


def test_text_under_min_summarization_length(mock_llm):
    short_text = "i" * 100

    mock_llm.predict.return_value = "This is a mock summary."

    node = TextNode(text=short_text, metadata={"h1": "Long Text"}, relationships={})
    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, min_summarization_length=200)

    summarized_nodes = summarizer.summarize_nodes(nodes)
    summary_nodes = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]

    assert len(summary_nodes) == 2
    assert summary_nodes[0].text == short_text
    assert summary_nodes[1].text == "This is a mock summary."


def test_recursive_splitting_and_summarization(mock_llm):
    mock_llm.predict.return_value = "Summarized recursive text"

    # Create a node that requires recursive splitting
    very_long_text = "sentence. " * 5000  # Adjust to require multiple splits

    node = TextNode(
        text=very_long_text, metadata={"h1": "Very Long Text"}, relationships={}
    )

    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Check that the summarizer handles multiple recursive splits
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) > 0
    # The summary should be significantly shorter
    assert len(summaries[0].text) < len(very_long_text)


def test_parent_child_relationships(mock_llm):
    mock_llm.predict.return_value = "Summarized text"

    # Create nodes with hierarchical relationships
    node1 = TextNode(
        text="Parent node text", metadata={"h1": "Parent"}, relationships={}
    )
    node2 = TextNode(
        text="Child node text",
        metadata={"h1": "Parent", "h2": "Child"},
        relationships={},
    )
    node3 = TextNode(
        text="Grandchild node text",
        metadata={"h1": "Parent", "h2": "Child", "h3": "Grandchild"},
        relationships={},
    )

    nodes = [node1, node2, node3]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Verify that parent-child relationships are correctly set in summaries
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 4  # Summaries for each level

    # Map summaries by their level
    summaries_by_level = {node.metadata.get(HEADING_LEVEL): node for node in summaries}

    # Check that child summaries have correct parent relationships
    assert (
        summaries_by_level[3].relationships[NodeRelationship.PARENT].node_id
        == summaries_by_level[2].node_id
    )
    assert (
        summaries_by_level[2].relationships[NodeRelationship.PARENT].node_id
        == summaries_by_level[1].node_id
    )
    assert (
        RelatedNodeInfo(node_id=summaries_by_level[2].node_id)
        in summaries_by_level[1].relationships[NodeRelationship.CHILD]
    )
    assert (
        RelatedNodeInfo(node_id=summaries_by_level[3].node_id)
        in summaries_by_level[2].relationships[NodeRelationship.CHILD]
    )


def test_multiple_child_nodes(mock_llm):
    mock_llm.predict.return_value = "Summarized text"

    # Create nodes with multiple child nodes
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
    node3 = TextNode(
        id_="node3", text="Child 3 text", metadata={"h1": "Parent"}, relationships={}
    )

    nodes = [node1, node2, node3]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 2  # One for each level

    # Verify parent-child relationships
    assert len(summaries[0].relationships[NodeRelationship.CHILD]) == 3
    assert (
        RelatedNodeInfo(node_id=node1.node_id)
        in summaries[0].relationships[NodeRelationship.CHILD]
    )
    assert (
        RelatedNodeInfo(node_id=node2.node_id)
        in summaries[0].relationships[NodeRelationship.CHILD]
    )
    assert (
        RelatedNodeInfo(node_id=node3.node_id)
        in summaries[0].relationships[NodeRelationship.CHILD]
    )


def test_no_nodes(mock_llm):
    # Test summarizer with an empty node list
    nodes: List[TextNode] = []

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Expect no summaries to be created
    assert len(summarized_nodes) == 0


def test_single_node_summarization(mock_llm):
    mock_llm.predict.return_value = "Summarized single node text"

    # Test summarization with a single node
    node = TextNode(
        text="This is a test node.", metadata={"h1": "Test Header"}, relationships={}
    )

    nodes = [node]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm, min_summarization_length=0)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Check that a summary is created
    summaries = [
        n for n in summarized_nodes if n.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 2

    # Verify the summary content
    expected_summary = "Summarized single node text"
    assert summaries[0].text == expected_summary


def test_nodes_with_missing_headers(mock_llm):
    mock_llm.predict.return_value = "Summarized text without headers"

    # Nodes without header metadata
    node1 = TextNode(
        text="Node 1 text without header",
        metadata={},
        relationships={NodeRelationship.NEXT: RelatedNodeInfo(node_id="node2")},
    )
    node2 = TextNode(
        id_="node2", text="Node 2 text without header", metadata={}, relationships={}
    )

    nodes = [node1, node2]

    summarizer = RecursiveNodeSummarizer(llm=mock_llm)
    summarized_nodes = summarizer.summarize_nodes(nodes)

    # Summaries should still be created
    summaries = [
        node
        for node in summarized_nodes
        if node.metadata.get(TYPE) == NODE_TYPE_SUMMARY
    ]
    assert len(summaries) == 1
