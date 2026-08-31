from unittest.mock import MagicMock, patch

from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID

from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager

_MARK_INGESTED = "swiss_ai_hub.pipeline.io.vector_store_io_manager.RefDoc.mark_ingested"
_ENSURE_CONNECTION = "swiss_ai_hub.pipeline.io.vector_store_io_manager.ensure_connection"

_STORE_NAME = "my_knowledge_db"


def _make_node(text: str, ref_doc_id: str | None = None, **metadata) -> TextNode:
    node = TextNode(text=text, metadata=metadata)
    if ref_doc_id:
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(node_id=ref_doc_id)
    return node


def _make_io_manager() -> VectorStoreIOManager:
    return VectorStoreIOManager(vector_store=MagicMock(), document_store_name=_STORE_NAME)


class TestMarkIngestedAfterWrite:
    """The whole point of marking here: the vector store write happens during output handling,
    so this is the earliest moment the document is genuinely retrievable."""

    def test_nodes_are_added_before_documents_are_marked(self) -> None:
        io_manager = _make_io_manager()
        calls = []
        io_manager.vector_store.add.side_effect = lambda nodes: calls.append("add")

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, side_effect=lambda **_: calls.append("mark") or True):
            io_manager.handle_output(MagicMock(), [_make_node("a", ref_doc_id="doc1")])

        assert calls == ["add", "mark"]

    def test_marks_each_distinct_document_once(self) -> None:
        io_manager = _make_io_manager()
        nodes = [
            _make_node("a", ref_doc_id="doc1"),
            _make_node("b", ref_doc_id="doc1"),
            _make_node("c", ref_doc_id="doc2"),
        ]

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=True) as mark_ingested:
            io_manager.handle_output(MagicMock(), nodes)

        assert mark_ingested.call_count == 2
        assert {call.kwargs["doc_id"] for call in mark_ingested.call_args_list} == {"doc1", "doc2"}
        assert {call.kwargs["db_alias"] for call in mark_ingested.call_args_list} == {_STORE_NAME}

    def test_marks_every_document_for_a_list_of_lists(self) -> None:
        io_manager = _make_io_manager()
        nodes = [[_make_node("a", ref_doc_id="doc1")], [_make_node("b", ref_doc_id="doc2")]]

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=True) as mark_ingested:
            io_manager.handle_output(MagicMock(), nodes)

        assert {call.kwargs["doc_id"] for call in mark_ingested.call_args_list} == {"doc1", "doc2"}

    def test_falls_back_to_document_id_metadata_when_no_source_relationship(self) -> None:
        io_manager = _make_io_manager()

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=True) as mark_ingested:
            io_manager.handle_output(MagicMock(), [_make_node("a", **{DOCUMENT_ID: "doc3"})])

        assert mark_ingested.call_args.kwargs["doc_id"] == "doc3"

    def test_empty_nodes_marks_nothing_and_writes_nothing(self) -> None:
        """A document that chunks to zero nodes is not retrievable, so it stays pending."""
        io_manager = _make_io_manager()

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED) as mark_ingested:
            io_manager.handle_output(MagicMock(), [])

        io_manager.vector_store.add.assert_not_called()
        mark_ingested.assert_not_called()

    def test_unknown_document_is_warned_about_not_raised(self) -> None:
        io_manager = _make_io_manager()
        context = MagicMock()

        with patch(_ENSURE_CONNECTION), patch(_MARK_INGESTED, return_value=False):
            io_manager.handle_output(context, [_make_node("a", ref_doc_id="ghost")])

        assert any("ghost" in str(call) for call in context.log.warning.call_args_list)
