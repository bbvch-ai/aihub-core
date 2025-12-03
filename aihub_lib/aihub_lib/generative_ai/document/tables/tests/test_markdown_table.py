"""Tests for markdown_table module - basic table utilities."""

import pandas as pd

from aihub_lib.generative_ai.document.tables.markdown_table import (
    apply_header_rows,
    create_markdown_table,
    has_integer_column_indices,
    parse_markdown_table,
    split_dataframe_into_chunks,
)


class TestHasIntegerColumnIndices:
    """Tests for has_integer_column_indices function."""

    def test_integer_columns_returns_true(self) -> None:
        """Test that DataFrame with integer columns returns True."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=[0, 1])
        assert has_integer_column_indices(df) is True

    def test_string_columns_returns_false(self) -> None:
        """Test that DataFrame with string columns returns False."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=["A", "B"])
        assert has_integer_column_indices(df) is False

    def test_mixed_columns_returns_false(self) -> None:
        """Test that DataFrame with mixed columns returns False."""
        df = pd.DataFrame([[1, 2], [3, 4]], columns=[0, "B"])
        assert has_integer_column_indices(df) is False


class TestApplyHeaderRows:
    """Tests for apply_header_rows function."""

    def test_single_header_row(self) -> None:
        """Test applying single header row."""
        df = pd.DataFrame([["H1", "H2"], ["A", "B"], ["C", "D"]], columns=[0, 1])
        result = apply_header_rows(df, 1)

        assert list(result.columns) == ["H1", "H2"]
        assert len(result) == 2
        assert result.iloc[0, 0] == "A"

    def test_multi_row_headers_joined(self) -> None:
        """Test that multi-row headers are joined with ' - ' separator."""
        df = pd.DataFrame([["Category", ""], ["Sub1", "Sub2"], ["A", "B"]], columns=[0, 1])
        result = apply_header_rows(df, 2)

        assert "Category - Sub1" in result.columns[0]
        assert " - Sub2" in result.columns[1]
        assert len(result) == 1
        assert result.iloc[0, 0] == "A"

    def test_zero_header_rows_returns_unchanged(self) -> None:
        """Test that zero header rows returns DataFrame unchanged."""
        df = pd.DataFrame([["A", "B"]], columns=[0, 1])
        result = apply_header_rows(df, 0)

        assert list(result.columns) == [0, 1]
        assert len(result) == 1


class TestCreateMarkdownTable:
    """Tests for create_markdown_table function."""

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
