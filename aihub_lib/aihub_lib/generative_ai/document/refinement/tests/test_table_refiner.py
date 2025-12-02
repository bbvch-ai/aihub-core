"""Tests for table_refiner module."""

from unittest.mock import MagicMock, patch

import pandas as pd

from aihub_lib.generative_ai.document.refinement.table_refiner import (
    _parse_markdown_table_to_dataframe,
    refine_document_tables,
)


class TestParseMarkdownTableToDataframe:
    """Tests for _parse_markdown_table_to_dataframe function."""

    def test_simple_table(self) -> None:
        """Test parsing a simple markdown table."""
        markdown = """| Header1 | Header2 |
|---------|---------|
| Cell1   | Cell2   |
| Cell3   | Cell4   |"""

        df = _parse_markdown_table_to_dataframe(markdown)

        assert df is not None
        assert df.shape == (3, 2)  # 3 rows (header + 2 data rows), 2 columns
        assert list(df.columns) == [0, 1]
        assert df.iloc[0, 0] == "Header1"
        assert df.iloc[0, 1] == "Header2"
        assert df.iloc[1, 0] == "Cell1"
        assert df.iloc[2, 1] == "Cell4"

    def test_table_with_alignment(self) -> None:
        """Test parsing table with alignment indicators."""
        markdown = """| Left | Center | Right |
|:-----|:------:|------:|
| A    | B      | C     |"""

        df = _parse_markdown_table_to_dataframe(markdown)

        assert df is not None
        assert df.shape == (2, 3)
        assert df.iloc[0, 0] == "Left"
        assert df.iloc[1, 2] == "C"

    def test_empty_table_returns_none(self) -> None:
        """Test that empty content returns None."""
        df = _parse_markdown_table_to_dataframe("")
        assert df is None

    def test_single_line_returns_none(self) -> None:
        """Test that single line (no separator) returns None."""
        markdown = "| Header1 | Header2 |"
        df = _parse_markdown_table_to_dataframe(markdown)
        assert df is None

    def test_no_separator_returns_none(self) -> None:
        """Test that table without separator line returns None."""
        markdown = """| Header1 | Header2 |
| Cell1   | Cell2   |"""
        df = _parse_markdown_table_to_dataframe(markdown)
        assert df is None

    def test_whitespace_handling(self) -> None:
        """Test that whitespace around cells is stripped."""
        markdown = """| Header1 | Header2 |
|---------|---------|
|   A   |   B   |"""

        df = _parse_markdown_table_to_dataframe(markdown)

        assert df is not None
        assert df.iloc[1, 0] == "A"
        assert df.iloc[1, 1] == "B"

    def test_mismatched_columns_skipped(self) -> None:
        """Test that rows with different column count are skipped."""
        markdown = """| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 |
| 6 | 7 | 8 |"""

        df = _parse_markdown_table_to_dataframe(markdown)

        assert df is not None
        # Header + 2 valid rows (row with 2 cells should be skipped)
        assert df.shape == (3, 3)


class TestRefineDocumentTables:
    """Tests for refine_document_tables function."""

    def test_no_tables_returns_unchanged(self) -> None:
        """Test that text without tables is returned unchanged."""
        text = "Some regular markdown text without any tables."
        mock_llm_config = MagicMock()

        result = refine_document_tables(text, mock_llm_config)

        assert result == text

    def test_finds_table_tags(self) -> None:
        """Test that table tags are found and processed."""
        text = """Some text before.
<table>| A | B |
|---|---|
| 1 | 2 |</table>
Some text after."""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            mock_create.return_value = "| A | B |\n|---|---|\n| 1 | 2 |"
            refine_document_tables(text, mock_llm_config)

            mock_create.assert_called_once()
            # Check that the dataframe passed has the expected shape
            call_args = mock_create.call_args
            df_arg = call_args[0][0]
            assert isinstance(df_arg, pd.DataFrame)
            assert df_arg.shape == (2, 2)  # Header row + 1 data row

    def test_multiple_tables(self) -> None:
        """Test processing multiple tables in same document."""
        text = """<table>| A |
|---|
| 1 |</table>
Middle text.
<table>| B |
|---|
| 2 |</table>"""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            mock_create.return_value = "| X |\n|---|\n| Y |"
            refine_document_tables(text, mock_llm_config)

            assert mock_create.call_count == 2

    def test_invalid_table_skipped(self) -> None:
        """Test that invalid tables are skipped without error."""
        text = """<table>Not a valid table</table>"""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            result = refine_document_tables(text, mock_llm_config)

            # create_markdown_table should not be called for invalid tables
            mock_create.assert_not_called()
            # Original text is preserved
            assert result == text

    def test_empty_table_skipped(self) -> None:
        """Test that empty tables are skipped."""
        text = """<table></table>"""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            result = refine_document_tables(text, mock_llm_config)

            mock_create.assert_not_called()
            assert result == text

    def test_table_splitting_creates_multiple_wrapped_tables(self) -> None:
        """Test that split tables are each wrapped in <table> tags."""
        text = """<table>| A | B |
|---|---|
| 1 | 2 |</table>"""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            # Simulate LLM splitting the table into two
            mock_create.return_value = "| A | B |\n|---|---|\n| 1 | 2 |\n\n| C | D |\n|---|---|\n| 3 | 4 |"
            result = refine_document_tables(text, mock_llm_config)

            # Both tables should be wrapped
            assert result.count("<table>") == 2
            assert result.count("</table>") == 2

    def test_preserves_surrounding_text(self) -> None:
        """Test that text before and after tables is preserved."""
        text = """Before table.
<table>| A |
|---|
| 1 |</table>
After table."""

        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner.create_markdown_table") as mock_create:
            mock_create.return_value = "| A |\n|---|\n| 1 |"
            result = refine_document_tables(text, mock_llm_config)

            assert "Before table." in result
            assert "After table." in result
