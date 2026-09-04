from unittest.mock import MagicMock, patch

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID

from swiss_ai_hub.pipeline.io.ingestion_marking import mark_ref_docs_as_ingested

_MODULE = "swiss_ai_hub.pipeline.io.ingestion_marking"
_MARK_INGESTED = f"{_MODULE}.RefDoc.mark_ingested"
_ENSURE_CONNECTION = f"{_MODULE}.MongoConnectionRegistry.ensure_alias"

_STORE_NAME = "my_knowledge_db"


def _make_node(text: str, ref_doc_id: str | None = None, **metadata) -> TextNode:
    node = TextNode(text=text, metadata=metadata)
    if ref_doc_id:
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=ref_doc_id)
    return node


class TestMarkRefDocsAsIngested:
    """A document counts as ingested only once its nodes are in the vector store; this is the step
    that says so, and it runs from the IO manager because that is where the write happens."""

    def test_marks_each_distinct_document_once(self) -> None:
        nodes = [
            _make_node("a", ref_doc_id="doc1"),
            _make_node("b", ref_doc_id="doc1"),
            _make_node("c", ref_doc_id="doc2"),
        ]

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=True) as mark_ingested:
            mark_ref_docs_as_ingested(nodes, _STORE_NAME, MagicMock())

        assert mark_ingested.call_count == 2
        assert {call.kwargs["doc_id"] for call in mark_ingested.call_args_list} == {"doc1", "doc2"}
        assert {call.kwargs["db_alias"] for call in mark_ingested.call_args_list} == {_STORE_NAME}

    def test_registers_the_per_database_alias_before_writing(self) -> None:
        """Each knowledge database is its own Mongo database, created long after startup."""
        with patch(_ENSURE_CONNECTION) as ensure_alias, patch(_MARK_INGESTED, return_value=True):
            mark_ref_docs_as_ingested([_make_node("a", ref_doc_id="doc1")], _STORE_NAME, MagicMock())

        ensure_alias.assert_called_once_with(_STORE_NAME)

    def test_falls_back_to_document_id_metadata_when_no_source_relationship(self) -> None:
        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=True) as mark_ingested:
            mark_ref_docs_as_ingested([_make_node("a", **{DOCUMENT_ID: "doc3"})], _STORE_NAME, MagicMock())

        assert mark_ingested.call_args.kwargs["doc_id"] == "doc3"

    def test_marks_nothing_when_there_are_no_nodes(self) -> None:
        """A document that chunks to zero nodes is not retrievable, so it stays pending."""
        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED) as mark_ingested:
            mark_ref_docs_as_ingested([], _STORE_NAME, MagicMock())

        mark_ingested.assert_not_called()

    def test_an_unknown_document_is_warned_about_rather_than_raised(self) -> None:
        log = MagicMock()

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=False):
            mark_ref_docs_as_ingested([_make_node("a", ref_doc_id="ghost")], _STORE_NAME, log)

        log.warning.assert_called_once()
        assert "ghost" in log.warning.call_args.args[0]
