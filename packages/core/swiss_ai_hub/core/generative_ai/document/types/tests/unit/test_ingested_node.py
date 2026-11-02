"""A record synced as markdown with frontmatter (a Jira issue, a Confluence page) keeps its fields in node metadata,
named by `excluded_embed_metadata_keys`. These tests pin that a node read back from the vector store carries them as
`record_fields`, apart from the platform's own keys, and gives them back when it is turned into a llama-index node."""

from llama_index.core.schema import NodeRelationship, NodeWithScore, RelatedNodeInfo, TextNode

from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    PAGE,
    SOURCE,
    TYPE,
    UPDATED_AT,
)

_RECORD_FIELDS = {"issue_type": "Bug", "labels": ["backend", "urgent"], "page_version": 3, "status": "To Do"}


def _stored_node(record_fields: dict, excluded_keys: list[str]) -> TextNode:
    return TextNode(
        id_="node-1",
        text="Steps to reproduce.",
        metadata={
            SOURCE: "ENG/ENG-2.md",
            NAMESPACE: "ENG",
            DOCUMENT_TITLE: "ENG-2: Tables",
            TYPE: "content",
            CREATED_AT: 1700000000,
            UPDATED_AT: 1700005000,
            INSERTED_AT: 1700010000,
            PAGE: 0,
            "content_hash": "abc",
            **record_fields,
        },
        excluded_embed_metadata_keys=excluded_keys,
        relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id="doc-1")},
    )


def test_the_frontmatter_keys_become_record_fields():
    node = IngestedNode.from_llama_index_node(_stored_node(_RECORD_FIELDS, list(_RECORD_FIELDS)))

    assert node.record_fields == _RECORD_FIELDS
    assert list(node.record_fields) == list(_RECORD_FIELDS)
    assert node.metadata == {PAGE: 0, "content_hash": "abc"}


def test_a_document_without_frontmatter_has_no_record_fields():
    node = IngestedNode.from_llama_index_node(_stored_node({}, []))

    assert node.record_fields == {}
    assert node.metadata == {PAGE: 0, "content_hash": "abc"}


def test_an_excluded_key_the_node_does_not_carry_is_ignored():
    node = IngestedNode.from_llama_index_node(_stored_node({"status": "Done"}, ["status", "priority"]))

    assert node.record_fields == {"status": "Done"}


def test_a_node_without_a_language_has_none():
    """Ingestion detects no language, so a node without one must not claim any."""
    assert IngestedNode.from_llama_index_node(_stored_node({}, [])).language is None


def test_the_record_fields_go_back_into_the_llama_index_metadata():
    """The reranker scores the llama-index node's text with its metadata, so it keeps seeing the fields."""
    node = IngestedNode.from_llama_index_node(_stored_node(_RECORD_FIELDS, list(_RECORD_FIELDS)))

    converted = node.to_llama_index_node_with_score()

    assert isinstance(converted, NodeWithScore)
    for key, value in _RECORD_FIELDS.items():
        assert converted.node.metadata[key] == value
    assert LANGUAGE in converted.node.metadata
