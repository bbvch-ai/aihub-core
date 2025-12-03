"""Tests for table_refiner module."""

from unittest.mock import MagicMock, patch

import pandas as pd

from aihub_lib.generative_ai.document.refinement.table_refiner import (
    HeaderAnalysis,
    TableBoundary,
    TableRefinementStats,
    TableSplitAnalysis,
    _format_table_with_row_indices,
    _parse_markdown_table_to_dataframe,
    _refine_markdown_table_with_stats,
    _reset_columns_to_data,
    refine_document_tables_with_metadata,
)


class TestFormatTableWithRowIndices:
    """Tests for _format_table_with_row_indices function."""

    def test_simple_table(self) -> None:
        """Test formatting a simple table."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=[0, 1])
        result = _format_table_with_row_indices(df)

        assert "[0] 1 | 2" in result
        assert "[1] 3 | 4" in result

    def test_handles_empty_cells(self) -> None:
        """Test that empty cells are represented correctly."""
        df = pd.DataFrame([["A", None], ["", "B"]], columns=[0, 1])
        result = _format_table_with_row_indices(df)

        assert "[0] A |" in result
        assert "[1]  | B" in result

    def test_handles_nan_values(self) -> None:
        """Test that NaN values are converted to empty strings."""
        df = pd.DataFrame([["A", float("nan")]], columns=[0, 1])
        result = _format_table_with_row_indices(df)

        assert "[0] A |" in result


class TestResetColumnsToData:
    """Tests for _reset_columns_to_data function."""

    def test_integer_columns_unchanged(self) -> None:
        """Test that DataFrame with integer columns is returned unchanged."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=[0, 1])
        result = _reset_columns_to_data(df)

        assert list(result.columns) == [0, 1]
        assert len(result) == 2

    def test_string_columns_converted_to_data_row(self) -> None:
        """Test that string column names are converted to a data row."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=["A", "B"])
        result = _reset_columns_to_data(df)

        assert list(result.columns) == [0, 1]
        assert len(result) == 3  # Original header becomes first row
        assert result.iloc[0, 0] == "A"
        assert result.iloc[0, 1] == "B"


class TestTableSplitAnalysisModels:
    """Tests for table split analysis Pydantic models."""

    def test_table_boundary_model(self) -> None:
        """Test TableBoundary model creation."""
        boundary = TableBoundary(start_row=5)
        assert boundary.start_row == 5

    def test_table_split_analysis_model(self) -> None:
        """Test TableSplitAnalysis model creation."""
        analysis = TableSplitAnalysis(
            tables=[TableBoundary(start_row=0), TableBoundary(start_row=10)],
            reasoning="Found two tables",
        )
        assert len(analysis.tables) == 2
        assert analysis.tables[0].start_row == 0
        assert analysis.tables[1].start_row == 10


class TestHeaderAnalysisModel:
    """Tests for header analysis Pydantic model."""

    def test_header_analysis_model(self) -> None:
        """Test HeaderAnalysis model creation."""
        analysis = HeaderAnalysis(num_header_rows=2, reasoning="Two header rows detected")
        assert analysis.num_header_rows == 2
        assert analysis.reasoning == "Two header rows detected"


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


class TestRefineMarkdownTableWithStats:
    """Tests for _refine_markdown_table_with_stats with LLM (mocked)."""

    def test_single_table_single_header(self) -> None:
        """Test LLM analysis returning single table with single header."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            result, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            mock_split.assert_called_once()
            mock_header.assert_called_once()
            assert "H1" in result
            assert "H2" in result

    def test_split_into_multiple_tables(self) -> None:
        """Test LLM analysis splitting into multiple tables."""
        df = pd.DataFrame(
            [["H1", "H2"], ["A", "B"], ["H3", "H4"], ["C", "D"]],
            columns=[0, 1],
        )
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two merged tables",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            result, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            # Should have two tables separated by double newline
            assert "\n\n" in result
            assert mock_header.call_count == 2

    def test_multi_row_headers_detected(self) -> None:
        """Test LLM detecting multi-row headers."""
        df = pd.DataFrame(
            [["Category", ""], ["Sub1", "Sub2"], ["A", "B"]],
            columns=[0, 1],
        )
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=2, reasoning="Two header rows")

            result, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            # Headers should be merged with " - "
            assert "Category - Sub1" in result or "Sub1" in result

    def test_llm_failure_falls_back_to_single_header(self) -> None:
        """Test that LLM failure falls back to single header row."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split:
            mock_split.side_effect = Exception("LLM error")

            result, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            # Should still produce valid markdown with first row as header
            assert "H1" in result
            assert "H2" in result

    def test_returns_stats_with_llm(self) -> None:
        """Test that stats are returned when LLM is used."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            content, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.original_rows == 2
            assert stats.was_split is False
            assert stats.tables_after_split == 1
            assert stats.header_rows_detected == [1]

    def test_stats_reflect_split(self) -> None:
        """Test that stats correctly reflect a split table."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"], ["H3", "H4"], ["C", "D"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.refinement.table_refiner._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two tables merged",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            content, stats = _refine_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.was_split is True
            assert stats.tables_after_split == 2
            assert len(stats.header_rows_detected) == 2
            assert stats.split_reasoning == "Two tables merged"


class TestRefineDocumentTablesWithMetadataContent:
    """Tests for refine_document_tables_with_metadata content output."""

    def test_no_tables_returns_unchanged(self) -> None:
        """Test that text without tables is returned unchanged."""
        text = "Some regular markdown text without any tables."
        mock_llm_config = MagicMock()

        result = refine_document_tables_with_metadata(text, mock_llm_config)

        assert result.content == text

    def test_finds_table_tags(self) -> None:
        """Test that table tags are found and processed."""
        text = """Some text before.
<table>| A | B |
|---|---|
| 1 | 2 |</table>
Some text after."""

        mock_llm_config = MagicMock()

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.return_value = ("| A | B |\n|---|---|\n| 1 | 2 |", None)
            refine_document_tables_with_metadata(text, mock_llm_config)

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

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.return_value = ("| X |\n|---|\n| Y |", None)
            refine_document_tables_with_metadata(text, mock_llm_config)

            assert mock_create.call_count == 2

    def test_invalid_table_skipped(self) -> None:
        """Test that invalid tables are skipped without error."""
        text = """<table>Not a valid table</table>"""

        mock_llm_config = MagicMock()

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            # _refine_markdown_table_with_stats should not be called for invalid tables
            mock_create.assert_not_called()
            # Original text is preserved
            assert result.content == text

    def test_empty_table_skipped(self) -> None:
        """Test that empty tables are skipped."""
        text = """<table></table>"""

        mock_llm_config = MagicMock()

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            mock_create.assert_not_called()
            assert result.content == text

    def test_table_splitting_creates_multiple_wrapped_tables(self) -> None:
        """Test that split tables are each wrapped in <table> tags."""
        text = """<table>| A | B |
|---|---|
| 1 | 2 |</table>"""

        mock_llm_config = MagicMock()

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            # Simulate LLM splitting the table into two
            mock_create.return_value = (
                "| A | B |\n|---|---|\n| 1 | 2 |\n\n| C | D |\n|---|---|\n| 3 | 4 |",
                None,
            )
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            # Both tables should be wrapped
            assert result.content.count("<table>") == 2
            assert result.content.count("</table>") == 2

    def test_preserves_surrounding_text(self) -> None:
        """Test that text before and after tables is preserved."""
        text = """Before table.
<table>| A |
|---|
| 1 |</table>
After table."""

        mock_llm_config = MagicMock()

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.return_value = ("| A |\n|---|\n| 1 |", None)
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            assert "Before table." in result.content
            assert "After table." in result.content


class TestRefineDocumentTablesWithMetadata:
    """Tests for refine_document_tables_with_metadata function."""

    def test_no_tables_returns_empty_metadata(self) -> None:
        """Test that text without tables returns empty metadata."""
        text = "Some regular markdown text without any tables."
        mock_llm_config = MagicMock()

        result = refine_document_tables_with_metadata(text, mock_llm_config)

        assert result.content == text
        assert result.metadata.tables_processed == 0
        assert result.metadata.tables_split == 0
        assert result.metadata.total_tables_after_split == 0
        assert result.metadata.table_stats == []

    def test_metadata_tracks_single_table(self) -> None:
        """Test that metadata tracks a single table correctly."""
        text = """<table>| A | B |
|---|---|
| 1 | 2 |</table>"""

        mock_llm_config = MagicMock()
        mock_stats = TableRefinementStats(
            original_rows=2,
            was_split=False,
            tables_after_split=1,
            header_rows_detected=[1],
            split_reasoning="Single table",
        )

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.return_value = ("| A | B |\n|---|---|\n| 1 | 2 |", mock_stats)
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            assert result.metadata.tables_processed == 1
            assert result.metadata.tables_split == 0
            assert result.metadata.total_tables_after_split == 1
            assert len(result.metadata.table_stats) == 1
            assert result.metadata.table_stats[0].was_split is False

    def test_metadata_tracks_split_table(self) -> None:
        """Test that metadata tracks a split table correctly."""
        text = """<table>| A | B |
|---|---|
| 1 | 2 |</table>"""

        mock_llm_config = MagicMock()
        mock_stats = TableRefinementStats(
            original_rows=4,
            was_split=True,
            tables_after_split=2,
            header_rows_detected=[1, 1],
            split_reasoning="Found two merged tables",
        )

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.return_value = (
                "| A | B |\n|---|---|\n| 1 | 2 |\n\n| C | D |\n|---|---|\n| 3 | 4 |",
                mock_stats,
            )
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            assert result.metadata.tables_processed == 1
            assert result.metadata.tables_split == 1
            assert result.metadata.total_tables_after_split == 2
            assert result.metadata.table_stats[0].was_split is True

    def test_metadata_aggregates_multiple_tables(self) -> None:
        """Test that metadata aggregates stats from multiple tables."""
        text = """<table>| A |
|---|
| 1 |</table>
<table>| B |
|---|
| 2 |</table>"""

        mock_llm_config = MagicMock()
        mock_stats_1 = TableRefinementStats(
            original_rows=2,
            was_split=True,
            tables_after_split=2,
            header_rows_detected=[1, 1],
            split_reasoning="Split first table",
        )
        mock_stats_2 = TableRefinementStats(
            original_rows=2,
            was_split=False,
            tables_after_split=1,
            header_rows_detected=[2],
            split_reasoning="Single table",
        )

        with patch(
            "aihub_lib.generative_ai.document.refinement.table_refiner._refine_markdown_table_with_stats"
        ) as mock_create:
            mock_create.side_effect = [
                ("| A |\n|---|\n| 1 |\n\n| A2 |\n|---|\n| 2 |", mock_stats_1),
                ("| B |\n|---|\n| 2 |", mock_stats_2),
            ]
            result = refine_document_tables_with_metadata(text, mock_llm_config)

            assert result.metadata.tables_processed == 2
            assert result.metadata.tables_split == 1  # Only first table was split
            assert result.metadata.total_tables_after_split == 3  # 2 + 1
            assert len(result.metadata.table_stats) == 2
