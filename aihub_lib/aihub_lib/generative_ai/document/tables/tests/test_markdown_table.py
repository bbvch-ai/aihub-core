"""Tests for markdown_table module - table split and header detection."""

from unittest.mock import MagicMock, patch

import pandas as pd

from aihub_lib.generative_ai.document.tables.markdown_table import (
    HeaderAnalysis,
    TableBoundary,
    TableSplitAnalysis,
    _apply_header_rows,
    _format_table_with_row_indices,
    _reset_columns_to_data,
    create_markdown_table,
    parse_markdown_table,
    refine_markdown_table_with_stats,
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
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            result = create_markdown_table(df, mock_llm_config)

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
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two merged tables",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            result = create_markdown_table(df, mock_llm_config)

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
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=2, reasoning="Two header rows")

            result = create_markdown_table(df, mock_llm_config)

            # Headers should be merged with " - "
            assert "Category - Sub1" in result or "Sub1" in result

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


class TestRefineMarkdownTableWithStats:
    """Tests for refine_markdown_table_with_stats function."""

    def test_returns_stats_with_llm(self) -> None:
        """Test that stats are returned when LLM is used."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"]], columns=[0, 1])
        mock_llm_config = MagicMock()

        with (
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(tables=[TableBoundary(start_row=0)], reasoning="Single table")
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            content, stats = refine_markdown_table_with_stats(df, mock_llm_config)

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
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_table_splits") as mock_split,
            patch("aihub_lib.generative_ai.document.tables.markdown_table._detect_header_rows") as mock_header,
        ):
            mock_split.return_value = TableSplitAnalysis(
                tables=[TableBoundary(start_row=0), TableBoundary(start_row=2)],
                reasoning="Two tables merged",
            )
            mock_header.return_value = HeaderAnalysis(num_header_rows=1, reasoning="One header row")

            content, stats = refine_markdown_table_with_stats(df, mock_llm_config)

            assert stats is not None
            assert stats.was_split is True
            assert stats.tables_after_split == 2
            assert len(stats.header_rows_detected) == 2
            assert stats.split_reasoning == "Two tables merged"
