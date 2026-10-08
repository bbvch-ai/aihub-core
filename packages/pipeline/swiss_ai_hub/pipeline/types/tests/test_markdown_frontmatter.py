"""A markdown file's frontmatter is split from its body and read into document fields and filterable metadata."""

from datetime import UTC, datetime

import pytest

from swiss_ai_hub.pipeline.types.malformed_frontmatter_error import MalformedFrontmatterError
from swiss_ai_hub.pipeline.types.markdown_frontmatter import MarkdownFrontmatter


def _parse(frontmatter: str, body: str = "# Body\n") -> MarkdownFrontmatter:
    parsed = MarkdownFrontmatter.from_markdown(f"---\n{frontmatter}---\n{body}")
    assert parsed is not None
    return parsed


def _epoch(*moment: int) -> int:
    return int(datetime(*moment, tzinfo=UTC).timestamp())


class TestFindingTheBlock:
    @pytest.mark.parametrize(
        "text",
        [
            "# Plain markdown\n\nNo frontmatter here.",
            "Intro\n---\ntitle: Not at the start\n---\n",
            "---\ntitle: Never closed\n\nBody",
            "--- title: on the opening line\n---\n",
            "",
        ],
    )
    def test_text_without_a_leading_block_has_no_frontmatter(self, text: str) -> None:
        assert MarkdownFrontmatter.from_markdown(text) is None

    def test_the_block_is_removed_from_the_body(self) -> None:
        parsed = MarkdownFrontmatter.from_markdown("---\ntitle: Report\n---\n# Heading\n\nText ---\n")

        assert parsed is not None
        assert parsed.body == "# Heading\n\nText ---\n"

    def test_an_empty_block_yields_only_the_body(self) -> None:
        parsed = MarkdownFrontmatter.from_markdown("---\n---\nBody")

        assert parsed == MarkdownFrontmatter(body="Body")

    @pytest.mark.parametrize(
        "text",
        [
            "\ufeff---\ntitle: Report\n---\nBody",
            "---\r\ntitle: Report\r\n---\r\nBody",
            "---\ntitle: Report\n...\nBody",
            "---  \ntitle: Report\n---\t\nBody",
        ],
    )
    def test_byte_order_mark_windows_line_endings_and_yaml_end_marker_are_understood(self, text: str) -> None:
        parsed = MarkdownFrontmatter.from_markdown(text)

        assert parsed is not None
        assert (parsed.title, parsed.body) == ("Report", "Body")

    def test_a_block_closing_at_the_end_of_the_file_leaves_an_empty_body(self) -> None:
        parsed = MarkdownFrontmatter.from_markdown("---\ntitle: Only metadata\n---")

        assert parsed is not None
        assert parsed.body == ""


class TestMalformedBlock:
    @pytest.mark.parametrize(
        "frontmatter",
        [
            "title: [unclosed\n",
            "key: value\n  bad indentation: here\n",
            "- a list\n- not a mapping\n",
            "Just a paragraph between two thematic breaks.\n",
        ],
    )
    def test_a_block_that_is_not_a_yaml_mapping_is_refused(self, frontmatter: str) -> None:
        with pytest.raises(MalformedFrontmatterError):
            MarkdownFrontmatter.from_markdown(f"---\n{frontmatter}---\nBody")


class TestReservedFields:
    def test_reserved_keys_become_document_fields_and_not_metadata(self) -> None:
        parsed = _parse(
            "title: 'ABC-123: Login fails'\n"
            "url: https://jira.example.com/browse/ABC-123\n"
            "created: 2026-09-01T09:00:00+02:00\n"
            "updated: 2026-09-30T14:05:00+02:00\n"
        )

        assert parsed.title == "ABC-123: Login fails"
        assert parsed.url == "https://jira.example.com/browse/ABC-123"
        assert parsed.created == _epoch(2026, 9, 1, 7)
        assert parsed.updated == _epoch(2026, 9, 30, 12, 5)
        assert parsed.metadata == {}
        assert parsed.skipped == {}

    def test_reserved_keys_are_matched_after_normalisation(self) -> None:
        parsed = _parse("Title: Report\nURL: https://example.com\n")

        assert (parsed.title, parsed.url) == ("Report", "https://example.com")

    def test_title_is_trimmed_and_a_number_is_read_as_text(self) -> None:
        assert _parse("title: '  Report  '\n").title == "Report"
        assert _parse("title: 2026\n").title == "2026"

    @pytest.mark.parametrize("title", ["''", "'   '", "[a, b]", "{nested: map}", "null"])
    def test_a_title_that_is_not_text_is_skipped(self, title: str) -> None:
        parsed = _parse(f"title: {title}\n")

        assert parsed.title is None
        assert "title" in parsed.skipped

    @pytest.mark.parametrize(
        "url",
        ["'javascript:alert(1)'", "ftp://example.com/file", "example.com/page", "'https://'", "42", "[https://a.ch]"],
    )
    def test_a_link_that_is_not_http_or_https_is_skipped(self, url: str) -> None:
        parsed = _parse(f"url: {url}\n")

        assert parsed.url is None
        assert "url" in parsed.skipped

    def test_a_title_or_link_too_long_to_store_on_every_chunk_is_skipped(self) -> None:
        """Both are stored twice per chunk and the title is embedded with each, so an unbounded one could fail the
        whole document instead of one key."""
        title = "t" * (MarkdownFrontmatter.MAX_TITLE_CHARACTERS + 1)
        url = "https://example.com/" + "p" * MarkdownFrontmatter.MAX_URL_CHARACTERS

        parsed = _parse(f"title: {title}\nurl: {url}\n")

        assert (parsed.title, parsed.url) == (None, None)
        assert "longer than" in parsed.skipped["title"]
        assert "longer than" in parsed.skipped["url"]

    def test_a_title_and_link_at_their_limits_are_kept(self) -> None:
        title = "t" * MarkdownFrontmatter.MAX_TITLE_CHARACTERS
        url = "https://example.com/" + "p" * (MarkdownFrontmatter.MAX_URL_CHARACTERS - len("https://example.com/"))

        parsed = _parse(f"title: {title}\nurl: {url}\n")

        assert (parsed.title, parsed.url) == (title, url)

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("2026-09-30", _epoch(2026, 9, 30)),
            ("2026-09-30T14:05:00+02:00", _epoch(2026, 9, 30, 12, 5)),
            ("2026-09-30T14:05:00Z", _epoch(2026, 9, 30, 14, 5)),
            ("2026-09-30T14:05:00", _epoch(2026, 9, 30, 14, 5)),
            ("'2026-09-30T14:05:00.000+0200'", _epoch(2026, 9, 30, 12, 5)),
            ("'2026-09-30'", _epoch(2026, 9, 30)),
        ],
    )
    def test_iso_8601_dates_become_epoch_seconds_with_utc_for_a_missing_zone(self, value: str, expected: int) -> None:
        assert _parse(f"updated: {value}\n").updated == expected

    @pytest.mark.parametrize("value", ["1759233900", "1759233900000", "'30.09.2026'", "yesterday", "true"])
    def test_numbers_and_non_iso_dates_are_skipped(self, value: str) -> None:
        parsed = _parse(f"created: {value}\n")

        assert parsed.created is None
        assert "ISO 8601" in parsed.skipped["created"]


class TestMetadata:
    def test_text_and_numbers_keep_their_type(self) -> None:
        parsed = _parse("project: ABC\npriority: 2\nestimate: 1.5\n")

        assert parsed.metadata == {"project": "ABC", "priority": 2, "estimate": 1.5}

    def test_true_and_false_become_text(self) -> None:
        """A retrieval filter cannot carry a boolean, so a flag is stored the way a filter can name it."""
        parsed = _parse("draft: false\nreviewed: true\n")

        assert parsed.metadata == {"draft": "false", "reviewed": "true"}

    def test_list_items_become_text(self) -> None:
        parsed = _parse("labels: [backend, urgent]\nmixed: [1, true, 2026-09-30]\nnone: []\n")

        assert parsed.metadata == {
            "labels": ["backend", "urgent"],
            "mixed": ["1", "true", "2026-09-30"],
            "none": [],
        }

    def test_a_date_becomes_iso_text(self) -> None:
        parsed = _parse("due: 2026-10-15\nreleased: 2026-10-15T08:00:00+00:00\n")

        assert parsed.metadata == {"due": "2026-10-15", "released": "2026-10-15T08:00:00+00:00"}

    @pytest.mark.parametrize(
        "frontmatter",
        [
            "owner:\n",
            "owner: {name: Ann}\n",
            "owner: [[nested], list]\n",
            "owner: [Ann, {name: Bob}]\n",
            "owner: [Ann, null]\n",
            "owner: 99999999999999999999\n",
            "owner: .nan\n",
        ],
    )
    def test_a_value_no_store_can_filter_on_is_skipped(self, frontmatter: str) -> None:
        parsed = _parse(frontmatter)

        assert parsed.metadata == {}
        assert "owner" in parsed.skipped

    @pytest.mark.parametrize(
        ("raw_key", "key"),
        [
            ("Project", "project"),
            ("Fix Version", "fix_version"),
            ("due-date", "due_date"),
            ("jira.key", "jira_key"),
            ("$meta", "meta"),
            ("(Project)", "project"),
            ("_private", "private"),
            ("Priorität", "prioritat"),
            ("  spaced  ", "spaced"),
        ],
    )
    def test_keys_are_normalised_to_lowercase_snake_case(self, raw_key: str, key: str) -> None:
        assert MarkdownFrontmatter.normalize_key(raw_key) == key
        assert _parse(f"'{raw_key}': value\n").metadata == {key: "value"}

    @pytest.mark.parametrize("raw_key", ["2fa", "日本語", "'---'", "''", "42", "'__'"])
    def test_a_key_with_no_usable_name_is_skipped(self, raw_key: str) -> None:
        parsed = _parse(f"{raw_key}: value\n")

        assert parsed.metadata == {}
        assert len(parsed.skipped) == 1

    @pytest.mark.parametrize(
        "raw_key",
        ["type", "language", "version", "namespace", "source", "Document Title", "reference_url", "h1"],
    )
    def test_a_name_the_platform_uses_is_skipped(self, raw_key: str) -> None:
        """A Jira `type: Bug` must not replace the content/summary type every retrieval filters on."""
        parsed = _parse(f"'{raw_key}': Bug\n")

        assert parsed.metadata == {}
        assert "platform already uses" in parsed.skipped[raw_key]

    def test_the_first_of_two_keys_with_the_same_normalised_name_wins(self) -> None:
        parsed = _parse("fix-version: '1.0'\nfix_version: '2.0'\nTitle: First\ntitle: Second\n")

        assert parsed.metadata == {"fix_version": "1.0"}
        assert parsed.title == "First"
        assert set(parsed.skipped) == {"fix_version", "title"}

    def test_a_skipped_value_does_not_claim_its_name(self) -> None:
        parsed = _parse("owner: {name: Ann}\nOwner: Ann\n")

        assert parsed.metadata == {"owner": "Ann"}

    def test_keys_beyond_the_size_budget_are_skipped_in_file_order(self) -> None:
        large_value = "x" * 3000
        parsed = _parse("".join(f"key_{index}: {large_value}\n" for index in range(4)))

        assert list(parsed.metadata) == ["key_0", "key_1"]
        assert set(parsed.skipped) == {"key_2", "key_3"}
