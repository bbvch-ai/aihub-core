from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, SOURCE

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.meta_utils import ref_doc_metadata_table


def _ref_doc(doc_id: str, metadata: dict) -> RefDocDocument:
    return RefDocDocument(id_=doc_id, text="content", metadata=metadata)


def test_ref_doc_metadata_table_handles_heterogeneous_metadata():
    """A fully ingested doc and a placeholder doc have different metadata keys; the table must
    still build (Dagster requires every record to share the same fields)."""
    ingested = _ref_doc(
        "doc-1",
        {NAMESPACE: "ns", SOURCE: "s3://b/ns/a.pdf", "language": "en", "version": 1},
    )
    placeholder = _ref_doc("doc-2", {NAMESPACE: "ns", SOURCE: "s3://b/ns/b.pdf"})

    table = ref_doc_metadata_table([ingested, placeholder])

    records = table.value.records
    assert len(records) == 2
    key_sets = {frozenset(record.data.keys()) for record in records}
    assert len(key_sets) == 1  # all records share identical fields


def test_ref_doc_metadata_table_empty():
    table = ref_doc_metadata_table([])
    assert table.value.records == []
