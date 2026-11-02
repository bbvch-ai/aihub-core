"""A markdown file's frontmatter becomes document metadata, and only ever its body is chunked (#1953)."""

from unittest.mock import patch

import pytest
from dagster import build_op_context
from llama_index.core.schema import MetadataMode
from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import (
    MarkdownStructuralNodeParser,
)
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_TITLE, SOURCE, SOURCE_ORIGIN

from swiss_ai_hub.pipeline.ops.document.apply_markdown_frontmatter import apply_markdown_frontmatter
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

_FRONTMATTER = (
    "---\n"
    "title: 'ABC-123: Login fails on Safari'\n"
    "url: https://jira.example.com/browse/ABC-123\n"
    "project: ABC\n"
    "labels: [backend, urgent]\n"
    "---\n"
)
_BODY = "# Symptoms\n\nUsers on Safari 17 cannot log in after the SSO change.\n"


def _ref_doc(text: str, uri: str = "s3://jira/ABC/ABC-123.md") -> RefDocDocument:
    return RefDocDocument(text=text, id_="doc", metadata={SOURCE: uri, DOCUMENT_TITLE: uri.rsplit("/", 1)[-1]})


class TestApplyMarkdownFrontmatter:
    def test_the_block_leaves_the_text_and_its_fields_become_document_metadata(self) -> None:
        result = apply_markdown_frontmatter(build_op_context(), _ref_doc(_FRONTMATTER + _BODY))

        assert result.value.text == _BODY
        assert result.value.metadata[DOCUMENT_TITLE] == "ABC-123: Login fails on Safari"
        assert result.value.metadata[SOURCE_ORIGIN] == "https://jira.example.com/browse/ABC-123"
        assert result.value.metadata["project"] == "ABC"
        assert result.value.metadata["labels"] == ["backend", "urgent"]
        assert result.metadata["Frontmatter metadata keys"].value == ["labels", "project"]

    def test_markdown_without_frontmatter_is_passed_through_as_is(self) -> None:
        ref_doc = _ref_doc(_BODY)

        result = apply_markdown_frontmatter(build_op_context(), ref_doc)

        assert result.value is ref_doc

    @pytest.mark.parametrize("uri", ["s3://kb/docs/report.pdf", "s3://kb/docs/notes.txt", "s3://kb/docs/slides.docx"])
    def test_a_file_that_is_not_markdown_is_never_read_for_frontmatter(self, uri: str) -> None:
        """Converters emit markdown too; a converted file opening with a horizontal rule is not YAML."""
        ref_doc = _ref_doc(_FRONTMATTER + _BODY, uri=uri)

        result = apply_markdown_frontmatter(build_op_context(), ref_doc)

        assert result.value is ref_doc

    def test_malformed_frontmatter_is_ingested_as_plain_text_with_a_warning(self) -> None:
        ref_doc = _ref_doc("---\ntitle: [unclosed\n---\n" + _BODY)
        context = build_op_context()

        with patch.object(context.log, "warning") as warning:
            result = apply_markdown_frontmatter(context, ref_doc)

        assert result.value is ref_doc
        warning.assert_called_once()
        assert "s3://jira/ABC/ABC-123.md" in warning.call_args.args[0]

    def test_each_skipped_key_is_warned_about(self) -> None:
        context = build_op_context()

        with patch.object(context.log, "warning") as warning:
            result = apply_markdown_frontmatter(context, _ref_doc("---\ntype: Bug\nurl: ftp://x\n---\n" + _BODY))

        assert warning.call_count == 2
        assert result.value.text == _BODY
        assert set(result.metadata["Skipped frontmatter keys"].value) == {"type", "url"}


class TestChunksOfAFrontmatterDocument:
    @staticmethod
    def _chunk(ref_doc: RefDocDocument) -> list:
        return MarkdownStructuralNodeParser.from_defaults(metadata=ref_doc.metadata).get_nodes_from_documents([ref_doc])

    def test_no_chunk_holds_the_frontmatter_and_every_chunk_carries_its_keys(self) -> None:
        applied = apply_markdown_frontmatter(build_op_context(), _ref_doc(_FRONTMATTER + _BODY)).value

        nodes = self._chunk(applied)

        assert nodes
        for node in nodes:
            assert "project:" not in node.text
            assert "---" not in node.text
            assert node.metadata["project"] == "ABC"
            assert node.metadata["labels"] == ["backend", "urgent"]
            assert node.metadata[DOCUMENT_TITLE] == "ABC-123: Login fails on Safari"

    def test_chunks_embed_the_title_but_not_the_custom_keys(self) -> None:
        applied = apply_markdown_frontmatter(build_op_context(), _ref_doc(_FRONTMATTER + _BODY)).value

        for node in self._chunk(applied):
            embedded_text = node.get_content(metadata_mode=MetadataMode.EMBED)
            assert "ABC-123: Login fails on Safari" in embedded_text
            assert "project" not in embedded_text
            assert "urgent" not in embedded_text

    def test_markdown_without_frontmatter_chunks_exactly_as_before(self) -> None:
        ref_doc = _ref_doc(_BODY)
        before = [(node.text, node.metadata) for node in self._chunk(ref_doc)]

        after = [
            (node.text, node.metadata)
            for node in self._chunk(apply_markdown_frontmatter(build_op_context(), ref_doc).value)
        ]

        assert after == before
