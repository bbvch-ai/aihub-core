"""Tests for text_refiner module."""

from unittest.mock import MagicMock, patch

from aihub_lib.generative_ai.document.refinement.text_refiner import (
    TextRefinementMetadata,
    TextRefinementResult,
    _extract_special_elements,
    _restore_special_elements,
    _split_into_chunks,
    refine_document_text,
    refine_document_text_with_metadata,
)


class TestExtractSpecialElements:
    """Tests for _extract_special_elements function."""

    def test_extracts_tables(self) -> None:
        """Test that tables are extracted and replaced with placeholders."""
        text = "Before <table>| A | B |</table> After"
        result, placeholders = _extract_special_elements(text)

        assert "<table>" not in result
        assert len(placeholders) == 1
        assert "__PLACEHOLDER_TABLE_0__" in result
        assert placeholders["__PLACEHOLDER_TABLE_0__"] == "<table>| A | B |</table>"

    def test_extracts_figures(self) -> None:
        """Test that figures are extracted and replaced with placeholders."""
        text = "Before <figure>![image](url)</figure> After"
        result, placeholders = _extract_special_elements(text)

        assert "<figure>" not in result
        assert len(placeholders) == 1
        assert "__PLACEHOLDER_FIGURE_0__" in result

    def test_extracts_multiple_elements(self) -> None:
        """Test extraction of multiple tables and figures."""
        text = "<table>T1</table> text <figure>F1</figure> more <table>T2</table>"
        result, placeholders = _extract_special_elements(text)

        assert len(placeholders) == 3
        # Tables are extracted first, then figures (order depends on regex substitution order)
        assert "__PLACEHOLDER_TABLE_" in result
        assert "__PLACEHOLDER_FIGURE_" in result
        assert "<table>" not in result
        assert "<figure>" not in result

    def test_no_special_elements(self) -> None:
        """Test that text without special elements is unchanged."""
        text = "Just plain text without tables or figures"
        result, placeholders = _extract_special_elements(text)

        assert result == text
        assert len(placeholders) == 0


class TestRestoreSpecialElements:
    """Tests for _restore_special_elements function."""

    def test_restores_placeholders(self) -> None:
        """Test that placeholders are restored to original content."""
        text = "Before __PLACEHOLDER_TABLE_0__ After"
        placeholders = {"__PLACEHOLDER_TABLE_0__": "<table>| A |</table>"}

        result = _restore_special_elements(text, placeholders)

        assert result == "Before <table>| A |</table> After"

    def test_restores_multiple_placeholders(self) -> None:
        """Test restoration of multiple placeholders."""
        text = "__PLACEHOLDER_TABLE_0__ and __PLACEHOLDER_FIGURE_1__"
        placeholders = {
            "__PLACEHOLDER_TABLE_0__": "<table>T</table>",
            "__PLACEHOLDER_FIGURE_1__": "<figure>F</figure>",
        }

        result = _restore_special_elements(text, placeholders)

        assert "<table>T</table>" in result
        assert "<figure>F</figure>" in result


class TestSplitIntoChunks:
    """Tests for _split_into_chunks function."""

    def test_small_text_single_chunk(self) -> None:
        """Test that small text returns single chunk."""
        text = "Short text"
        token_counter = lambda x: len(x.split())  # noqa: E731

        chunks = _split_into_chunks(text, token_counter, max_tokens=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_large_text_multiple_chunks(self) -> None:
        """Test that large text is split into multiple chunks."""
        paragraphs = [f"Paragraph {i} with some content." for i in range(20)]
        text = "\n\n".join(paragraphs)
        token_counter = lambda x: len(x.split())  # noqa: E731

        chunks = _split_into_chunks(text, token_counter, max_tokens=20)

        assert len(chunks) > 1

    def test_respects_paragraph_boundaries(self) -> None:
        """Test that chunks don't break mid-paragraph."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        token_counter = lambda x: len(x.split())  # noqa: E731

        chunks = _split_into_chunks(text, token_counter, max_tokens=5)

        # Each chunk should be a complete paragraph
        for chunk in chunks:
            assert chunk.count("\n\n") == 0 or chunk.endswith(".")


class TestRefineDocumentText:
    """Tests for refine_document_text function."""

    def test_returns_refined_text(self) -> None:
        """Test that refined text is returned."""
        text = "Some text to refine"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(10))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            mock_refine.return_value = "Refined text"
            result = refine_document_text(text, mock_llm_config)

            assert result == "Refined text"

    def test_preserves_tables(self) -> None:
        """Test that tables are preserved during refinement."""
        text = "Before <table>| A | B |</table> After"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(10))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            # Mock returns text with placeholder intact
            mock_refine.side_effect = lambda chunk, _: chunk
            result = refine_document_text(text, mock_llm_config)

            assert "<table>| A | B |</table>" in result


class TestRefineDocumentTextWithMetadata:
    """Tests for refine_document_text_with_metadata function."""

    def test_returns_result_with_metadata(self) -> None:
        """Test that result includes both content and metadata."""
        text = "Some text to refine"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(10))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            mock_refine.return_value = "Refined text"
            result = refine_document_text_with_metadata(text, mock_llm_config)

            assert isinstance(result, TextRefinementResult)
            assert result.content == "Refined text"
            assert isinstance(result.metadata, TextRefinementMetadata)

    def test_metadata_tracks_lengths(self) -> None:
        """Test that metadata tracks original and refined lengths."""
        text = "Original text here"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(10))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            mock_refine.return_value = "Shorter"
            result = refine_document_text_with_metadata(text, mock_llm_config)

            assert result.metadata.original_length == len(text)
            assert result.metadata.refined_length == len("Shorter")

    def test_metadata_tracks_chunks(self) -> None:
        """Test that metadata tracks chunk processing."""
        paragraphs = [f"Paragraph {i}." for i in range(5)]
        text = "\n\n".join(paragraphs)
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(5))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            mock_refine.side_effect = lambda chunk, _: chunk
            result = refine_document_text_with_metadata(text, mock_llm_config, max_chunk_tokens=3)

            assert result.metadata.chunks_processed >= 1

    def test_metadata_tracks_failed_chunks(self) -> None:
        """Test that metadata tracks failed chunk refinements."""
        text = "Some text"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(5))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            # Chunk refinement fails
            mock_refine.side_effect = Exception("LLM error")
            result = refine_document_text_with_metadata(text, mock_llm_config)

            # The single chunk should have failed
            assert result.metadata.chunks_failed == 1
            assert result.metadata.chunks_processed == 1
            # Original text should be preserved on failure
            assert result.content == text

    def test_metadata_counts_tables_and_figures(self) -> None:
        """Test that metadata counts preserved tables and figures."""
        text = "<table>T1</table> text <figure>F1</figure> more <table>T2</table>"
        mock_llm_config = MagicMock()
        mock_llm_config.token_counter.return_value = list(range(10))

        with patch("aihub_lib.generative_ai.document.refinement.text_refiner._refine_chunk") as mock_refine:
            mock_refine.side_effect = lambda chunk, _: chunk
            result = refine_document_text_with_metadata(text, mock_llm_config)

            assert result.metadata.tables_preserved == 2
            assert result.metadata.figures_preserved == 1
