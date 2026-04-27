import pytest

from swiss_ai_hub.core.generative_ai.utils.path_utils import (
    decode_partition_key,
    encode_partition_key,
)


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
