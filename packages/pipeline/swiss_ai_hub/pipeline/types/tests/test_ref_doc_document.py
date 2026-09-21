from datetime import UTC, datetime

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import IS_INGESTED, SOURCE

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


def _make_data_lake_file() -> DataLakeFile:
    now = int(datetime.now(tz=UTC).timestamp())
    return DataLakeFile(
        name="report.pdf",
        namespace="docs",
        filetype="pdf",
        uri="s3://bucket/docs/report.pdf",
        size=1024,
        created=now,
        updated=now,
        content_type="application/pdf",
        owner="test",
        hash="abc123",
        metadata={},
    )


class TestAddMetadataFromDataLakeFile:
    def test_parsed_document_is_not_yet_ingested(self) -> None:
        """A parsed document has markdown but no embeddings, so it is not queryable yet.
        The flag is flipped by VectorStoreIOManager once the nodes land in the vector store."""
        ref_doc = RefDocDocument(text="# Parsed").add_metadata_from_data_lake_file(_make_data_lake_file())

        assert ref_doc.metadata[IS_INGESTED] is False

    def test_keeps_enriching_the_remaining_metadata(self) -> None:
        ref_doc = RefDocDocument(text="# Parsed").add_metadata_from_data_lake_file(_make_data_lake_file())

        assert ref_doc.metadata[SOURCE] == "s3://bucket/docs/report.pdf"
        assert ref_doc.namespace == "docs"
        assert ref_doc.hash == "abc123"
