from datetime import UTC, datetime

from llama_index.core.schema import MetadataMode
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_TITLE,
    IS_INGESTED,
    SOURCE,
    SOURCE_ORIGIN,
    UPDATED_AT,
)

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.markdown_frontmatter import MarkdownFrontmatter
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


class TestWithFrontmatter:
    @staticmethod
    def _parsed_markdown() -> RefDocDocument:
        return RefDocDocument(text="raw").add_metadata_from_data_lake_file(_make_data_lake_file())

    def test_the_body_replaces_the_text_and_the_original_is_untouched(self) -> None:
        original = self._parsed_markdown()

        applied = original.with_frontmatter(MarkdownFrontmatter(body="# Body"))

        assert applied.text == "# Body"
        assert original.text == "raw"
        assert applied.id_ == original.id_

    def test_frontmatter_fields_win_over_the_data_lake_file(self) -> None:
        frontmatter = MarkdownFrontmatter(
            body="# Body", title="ABC-123", url="https://jira.example.com/browse/ABC-123", created=100, updated=200
        )

        applied = self._parsed_markdown().with_frontmatter(frontmatter)

        assert applied.metadata[DOCUMENT_TITLE] == "ABC-123"
        assert applied.metadata[SOURCE_ORIGIN] == "https://jira.example.com/browse/ABC-123"
        assert (applied.metadata[CREATED_AT], applied.metadata[UPDATED_AT]) == (100, 200)

    def test_a_field_the_frontmatter_lacks_keeps_the_data_lake_value(self) -> None:
        original = self._parsed_markdown()

        applied = original.with_frontmatter(MarkdownFrontmatter(body="# Body"))

        assert applied.metadata == original.metadata

    def test_custom_keys_are_stored_but_left_out_of_the_embedded_text(self) -> None:
        frontmatter = MarkdownFrontmatter(body="# Body", title="ABC-123", metadata={"project": "ABC", "labels": ["ui"]})

        applied = self._parsed_markdown().with_frontmatter(frontmatter)
        embedded_text = applied.get_content(metadata_mode=MetadataMode.EMBED)

        assert applied.metadata["project"] == "ABC"
        assert applied.metadata["labels"] == ["ui"]
        assert "project" not in embedded_text
        assert "labels" not in embedded_text
        assert "ABC-123" in embedded_text
