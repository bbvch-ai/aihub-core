import pytest

from swiss_ai_hub.core.generative_ai.utils.path_utils import (
    create_figures_folder_name,
    decode_partition_key,
    encode_partition_key,
)


class TestCreateFiguresFolderName:
    def test_filename_with_double_dot_is_accepted(self) -> None:
        result = create_figures_folder_name("s3://bucket/dir/Kabelliste Geb..pdf")
        assert result == "s3://bucket/dir/__figures__/Kabelliste_Geb__pdf"

    def test_rejects_parent_traversal(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            create_figures_folder_name("s3://bucket/dir/..")

    def test_rejects_single_dot(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            create_figures_folder_name("s3://bucket/dir/.")

    @pytest.mark.parametrize("file_name", ["a\\b.pdf", "..\\etc\\passwd"])
    def test_rejects_backslash_separator(self, file_name: str) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            create_figures_folder_name(f"s3://bucket/dir/{file_name}")

    def test_rejects_uri_without_slash(self) -> None:
        with pytest.raises(ValueError, match="Invalid URI"):
            create_figures_folder_name("nofileonly")


class TestEncodePartitionKey:
    """Tests for encode_partition_key function."""

    def test_spaces_encoded(self) -> None:
        assert encode_partition_key("dir name/file name.pdf") == "dir%20name/file%20name.pdf"

    def test_commas_encoded(self) -> None:
        assert encode_partition_key("Q1, 2024/report.pdf") == "Q1%2C%202024/report.pdf"

    def test_slashes_preserved(self) -> None:
        assert encode_partition_key("a/b/c/file.pdf") == "a/b/c/file.pdf"

    def test_safe_chars_preserved(self) -> None:
        assert encode_partition_key("dir/file_name-v2~draft.pdf") == "dir/file_name-v2~draft.pdf"

    def test_colons_preserved(self) -> None:
        assert encode_partition_key("s3://bucket/file.pdf") == "s3://bucket/file.pdf"

    def test_url_reserved_chars_encoded(self) -> None:
        result = encode_partition_key("dir/file?x=1&y=2#section")
        assert "%3F" in result  # ?
        assert "%3D" in result  # =
        assert "%26" in result  # &
        assert "%23" in result  # #

    def test_percent_encoded(self) -> None:
        assert encode_partition_key("file%20name") == "file%2520name"

    def test_s3_uri(self) -> None:
        result = encode_partition_key("s3://bucket/dir/Annual Report.pdf")
        assert result == "s3://bucket/dir/Annual%20Report.pdf"

    def test_empty_string(self) -> None:
        assert encode_partition_key("") == ""

    def test_no_encoding_needed(self) -> None:
        path = "projects/2024/report_final.pdf"
        assert encode_partition_key(path) == path


class TestDecodePartitionKey:
    """Tests for decode_partition_key function."""

    def test_spaces_decoded(self) -> None:
        assert decode_partition_key("dir%20name/file%20name.pdf") == "dir name/file name.pdf"

    def test_commas_decoded(self) -> None:
        assert decode_partition_key("Q1%2C%202024/report.pdf") == "Q1, 2024/report.pdf"

    def test_plain_key_unchanged(self) -> None:
        assert decode_partition_key("a/b/c/file.pdf") == "a/b/c/file.pdf"

    def test_empty_string(self) -> None:
        assert decode_partition_key("") == ""


class TestPartitionKeyRoundTrip:
    """Verify encode/decode are perfect inverses."""

    @pytest.mark.parametrize(
        "path",
        [
            "simple/path.pdf",
            "Company Docs/Q1, 2024/Annual Report.pdf",
            "dir with spaces/sub dir/file+name.pdf",
            "special/#hash/file?query=1&x=2.pdf",
            "percent%already/file.pdf",
            "unicode/café/résumé.pdf",
            "",
        ],
    )
    def test_roundtrip(self, path: str) -> None:
        assert decode_partition_key(encode_partition_key(path)) == path
