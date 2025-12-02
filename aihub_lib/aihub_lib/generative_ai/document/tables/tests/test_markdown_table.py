"""Tests for markdown_table module - all three refinement steps."""

from unittest.mock import MagicMock, patch

import pandas as pd

from aihub_lib.generative_ai.document.tables.markdown_table import (
    ColumnAlignmentAnalysis,
    ColumnCorrection,
    HeaderAnalysis,
    TableBoundary,
    TableSplitAnalysis,
    _apply_column_corrections,
    _apply_header_rows,
    _format_table_with_row_indices,
    _reset_columns_to_data,
    create_markdown_table,
    create_markdown_table_with_stats,
    parse_markdown_table,
    split_dataframe_into_chunks,
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


class TestApplyHeaderRows:
    """Tests for _apply_header_rows function."""

    def test_single_header_row(self) -> None:
        """Test applying single header row."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"], ["C", "D"]], columns=[0, 1])
        result = _apply_header_rows(df, 1)

        assert list(result.columns) == ["H1", "H2"]
        assert len(result) == 2
        assert result.iloc[0, 0] == "A"

    def test_multi_row_headers_joined(self) -> None:
        """Test that multi-row headers are joined with ' - ' separator."""
        df = pd.DataFrame([["Category", ""], ["Sub1", "Sub2"], ["A", "B"]], columns=[0, 1])
        result = _apply_header_rows(df, 2)

        assert "Category - Sub1" in result.columns[0]
        assert " - Sub2" in result.columns[1]
        assert len(result) == 1
        assert result.iloc[0, 0] == "A"

    def test_zero_header_rows_returns_unchanged(self) -> None:
        """Test that zero header rows returns DataFrame unchanged."""
        df = pd.DataFrame([["A", "B"]], columns=[0, 1])
        result = _apply_header_rows(df, 0)

        assert list(result.columns) == [0, 1]
        assert len(result) == 1


class TestApplyColumnCorrections:
    """Tests for _apply_column_corrections function (Step 3)."""

    def test_single_correction(self) -> None:
        """Test applying a single column correction."""
        df = pd.DataFrame([["Header1", "Header2", ""], ["Value", "", ""]], columns=[0, 1, 2])
        corrections = [ColumnCorrection(row=1, from_col=0, to_col=1)]

        result = _apply_column_corrections(df, corrections)

        assert result.iloc[1, 0] == ""
        assert result.iloc[1, 1] == "Value"

    def test_multiple_corrections(self) -> None:
        """Test applying multiple column corrections."""
        df = pd.DataFrame([["A", "", "B"], ["", "C", ""]], columns=[0, 1, 2])
        corrections = [
            ColumnCorrection(row=0, from_col=2, to_col=1),
            ColumnCorrection(row=1, from_col=1, to_col=0),
        ]

        result = _apply_column_corrections(df, corrections)

        assert result.iloc[0, 1] == "B"
        assert result.iloc[0, 2] == ""
        assert result.iloc[1, 0] == "C"
        assert result.iloc[1, 1] == ""

    def test_out_of_bounds_row_skipped(self) -> None:
        """Test that corrections with out-of-bounds row are skipped."""
        df = pd.DataFrame([["A", "B"]], columns=[0, 1])
        corrections = [ColumnCorrection(row=5, from_col=0, to_col=1)]

        result = _apply_column_corrections(df, corrections)

        # DataFrame should be unchanged
        assert result.iloc[0, 0] == "A"
        assert result.iloc[0, 1] == "B"

    def test_out_of_bounds_column_skipped(self) -> None:
        """Test that corrections with out-of-bounds columns are skipped."""
        df = pd.DataFrame([["A", "B"]], columns=[0, 1])
        corrections = [ColumnCorrection(row=0, from_col=0, to_col=5)]

        result = _apply_column_corrections(df, corrections)

        # DataFrame should be unchanged
        assert result.iloc[0, 0] == "A"

    def test_empty_corrections_list(self) -> None:
        """Test that empty corrections list returns DataFrame unchanged."""
        df = pd.DataFrame([["A", "B"]], columns=[0, 1])
        result = _apply_column_corrections(df, [])

        assert result.iloc[0, 0] == "A"
        assert result.iloc[0, 1] == "B"

    def test_original_dataframe_not_modified(self) -> None:
        """Test that the original DataFrame is not modified."""
        df = pd.DataFrame([["A", ""]], columns=[0, 1])
        original_value = df.iloc[0, 0]
        corrections = [ColumnCorrection(row=0, from_col=0, to_col=1)]

        _apply_column_corrections(df, corrections)

        assert df.iloc[0, 0] == original_value


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


class TestColumnAlignmentModels:
    """Tests for column alignment Pydantic models."""

    def test_column_correction_model(self) -> None:
        """Test ColumnCorrection model creation."""
        correction = ColumnCorrection(row=1, from_col=2, to_col=3)
        assert correction.row == 1
        assert correction.from_col == 2
        assert correction.to_col == 3

    def test_column_alignment_analysis_model(self) -> None:
        """Test ColumnAlignmentAnalysis model creation."""
        analysis = ColumnAlignmentAnalysis(
            corrections=[ColumnCorrection(row=0, from_col=1, to_col=2)],
            reasoning="One misaligned value",
        )
        assert len(analysis.corrections) == 1
        assert analysis.reasoning == "One misaligned value"

    def test_empty_corrections_list(self) -> None:
        """Test ColumnAlignmentAnalysis with empty corrections."""
        analysis = ColumnAlignmentAnalysis(corrections=[], reasoning="Table is correctly aligned")
        assert len(analysis.corrections) == 0


class TestCreateMarkdownTableWithoutLLM:
    """Tests for create_markdown_table without LLM (fallback behavior)."""

    def test_empty_dataframe(self) -> None:
        """Test that empty DataFrame returns empty markdown."""
        df = pd.DataFrame()
        result = create_markdown_table(df)
        assert result is not None

    def test_integer_columns_use_first_row_as_header(self) -> None:
        """Test that integer columns trigger first row as header."""
        df = pd.DataFrame([["Header1", "Header2"], ["A", "B"]], columns=[0, 1])
        result = create_markdown_table(df)

        assert "Header1" in result
        assert "Header2" in result

    def test_string_columns_kept_as_is(self) -> None:
        """Test that string columns are kept without modification."""
        df = pd.DataFrame([["A", "B"]], columns=["Col1", "Col2"])
        result = create_markdown_table(df)

        assert "Col1" in result
        assert "Col2" in result


class TestCreateMarkdownTableWithLLM:
    """Tests for create_markdown_table with LLM (mocked)."""

    def test_single_table_single_header(self) -> None:
        """Test LLM analysis returning single table with single header."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            mock_align.return_value = ColumnAlignmentAnalysis(corrections=[], reasoning="Aligned")

            result = create_markdown_table(df, mock_llm_config)

            mock_split.assert_called_once()
            mock_header.assert_called_once()
            mock_align.assert_called_once()
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
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two merged tables",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            mock_align.return_value = ColumnAlignmentAnalysis(corrections=[], reasoning="Aligned")

            result = create_markdown_table(df, mock_llm_config)

            # Should have two tables separated by double newline
            assert "\n\n" in result
            assert mock_header.call_count == 2
            assert mock_align.call_count == 2

    def test_multi_row_headers_detected(self) -> None:
        """Test LLM detecting multi-row headers."""
        df = pd.DataFrame(
            [["Category", ""], ["Sub1", "Sub2"], ["A", "B"]],
            columns=[0, 1],
        )
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=2, reasoning="Two header rows")
            mock_align.return_value = ColumnAlignmentAnalysis(corrections=[], reasoning="Aligned")

            result = create_markdown_table(df, mock_llm_config)

            # Headers should be merged with " - "
            assert "Category - Sub1" in result or "Sub1" in result

    def test_column_corrections_applied(self) -> None:
        """Test that column corrections are applied."""
        df = pd.DataFrame([["H1", "H2"], ["Value", ""]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            # Move value from col 0 to col 1 in row 1 (data row)
            mock_align.return_value = ColumnAlignmentAnalysis(
                corrections=[ColumnCorrection(row=1, from_col=0, to_col=1)],
                reasoning="Value in wrong column",
            )

            result = create_markdown_table(df, mock_llm_config)

            # Value should have been moved
            assert "Value" in result

    def test_llm_failure_falls_back_to_single_header(self) -> None:
        """Test that LLM failure falls back to single header row."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split:
            mock_split.side_effect = Exception("LLM error")

            result = create_markdown_table(df, mock_llm_config)

            # Should still produce valid markdown with first row as header
            assert "H1" in result
            assert "H2" in result


class TestParseMarkdownTable:
    """Tests for parse_markdown_table function."""

    def test_simple_table(self) -> None:
        """Test parsing a simple markdown table."""
        markdown = "| A | B |\n|---|---|\n| 1 | 2 |"
        df = parse_markdown_table(markdown)

        assert df is not None
        assert df.shape == (1, 2)
        assert list(df.columns) == ["A", "B"]
        assert df.iloc[0, 0] == "1"

    def test_empty_content_returns_none(self) -> None:
        """Test that empty content returns None."""
        assert parse_markdown_table("") is None

    def test_single_line_returns_none(self) -> None:
        """Test that single line returns None."""
        assert parse_markdown_table("| A | B |") is None

    def test_no_data_rows(self) -> None:
        """Test table with only header and separator."""
        markdown = "| A | B |\n|---|---|"
        df = parse_markdown_table(markdown)

        assert df is not None
        assert df.shape == (0, 2)


class TestSplitDataframeIntoChunks:
    """Tests for split_dataframe_into_chunks function."""

    def test_small_table_single_chunk(self) -> None:
        """Test that small table returns single chunk."""
        df = pd.DataFrame([["A", "B"]], columns=["Col1", "Col2"])
        token_counter = lambda x: len(x)  # noqa: E731

        chunks = split_dataframe_into_chunks(df, max_tokens=1000, token_counter=token_counter)

        assert len(chunks) == 1

    def test_large_table_multiple_chunks(self) -> None:
        """Test that large table is split into multiple chunks."""
        # Create a table with many rows
        data = [[f"Value{i}", f"Data{i}"] for i in range(100)]
        df = pd.DataFrame(data, columns=["Col1", "Col2"])
        token_counter = lambda x: len(x)  # noqa: E731

        chunks = split_dataframe_into_chunks(df, max_tokens=200, token_counter=token_counter)

        assert len(chunks) > 1
        # Each chunk should have the header
        for chunk in chunks:
            assert "Col1" in chunk
            assert "Col2" in chunk

    def test_each_chunk_has_headers(self) -> None:
        """Test that each chunk includes the table headers."""
        data = [[f"V{i}", f"D{i}"] for i in range(50)]
        df = pd.DataFrame(data, columns=["Header1", "Header2"])
        token_counter = lambda x: len(x)  # noqa: E731

        chunks = split_dataframe_into_chunks(df, max_tokens=150, token_counter=token_counter)

        for chunk in chunks:
            assert "Header1" in chunk
            assert "Header2" in chunk


class TestCreateMarkdownTableWithStats:
    """Tests for create_markdown_table_with_stats function."""

    def test_returns_none_stats_without_llm(self) -> None:
        """Test that stats are None when no LLM config is provided."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])

        content, stats = create_markdown_table_with_stats(df)

        assert "H1" in content
        assert stats is None

    def test_returns_stats_with_llm(self) -> None:
        """Test that stats are returned when LLM is used."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            mock_align.return_value = ColumnAlignmentAnalysis(corrections=[], reasoning="Aligned")

            content, stats = create_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.original_rows == 2
            assert stats.was_split is False
            assert stats.tables_after_split == 1
            assert stats.header_rows_detected == [1]
            assert stats.column_corrections_applied == 0

    def test_stats_reflect_split(self) -> None:
        """Test that stats correctly reflect a split table."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"], ["H3", "H4"], ["C", "D"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two tables merged",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            mock_align.return_value = ColumnAlignmentAnalysis(corrections=[], reasoning="Aligned")

            content, stats = create_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.was_split is True
            assert stats.tables_after_split == 2
            assert len(stats.header_rows_detected) == 2
            assert stats.split_reasoning == "Two tables merged"

    def test_stats_reflect_column_corrections(self) -> None:
        """Test that stats correctly reflect column corrections."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
            patch(
                "aihub_lib.generative_ai.document.tables.markdown_table._detect_column_alignment_errors"
            ) as mock_align,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")
            mock_align.return_value = ColumnAlignmentAnalysis(
                corrections=[
                    ColumnCorrection(row=1, from_col=0, to_col=1),
                    ColumnCorrection(row=1, from_col=1, to_col=0),
                ],
                reasoning="Swapped columns",
            )

            content, stats = create_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.column_corrections_applied == 2
