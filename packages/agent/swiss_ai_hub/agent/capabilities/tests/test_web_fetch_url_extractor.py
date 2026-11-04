import pytest
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.extracted_urls import ExtractedUrls
from swiss_ai_hub.agent.capabilities.web_fetch.url_extractor import UrlExtractor


def extract(text: str) -> ExtractedUrls:
    return UrlExtractor.classify(UrlExtractor.find(text))


class TestDetection:
    def test_finds_every_url_not_just_the_first(self):
        result = extract("Compare https://a.example/one and http://b.example/two please")

        assert result.urls == ["https://a.example/one", "http://b.example/two"]

    def test_finds_nothing_in_plain_text(self):
        result = extract("What is the capital of Switzerland?")

        assert result.urls == []
        assert result.failures == []

    def test_keeps_message_order(self):
        result = extract("https://c.example https://a.example https://b.example")

        assert result.urls == ["https://c.example", "https://a.example", "https://b.example"]

    def test_deduplicates_repeated_urls(self):
        result = extract("See https://a.example/x, again https://a.example/x.")

        assert result.urls == ["https://a.example/x"]

    def test_matches_the_scheme_case_insensitively(self):
        assert extract("HTTPS://Example.com/Page").urls == ["HTTPS://Example.com/Page"]

    def test_keeps_query_and_fragment(self):
        url = "https://example.com/search?q=swiss+ai&page=2#results"

        assert extract(f"Look at {url}").urls == [url]


class TestSurroundingPunctuation:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Read https://example.com/page.", "https://example.com/page"),
            ("Read https://example.com/page, then answer", "https://example.com/page"),
            ("Is it https://example.com/page?", "https://example.com/page"),
            ("(see https://example.com/page)", "https://example.com/page"),
            ('"https://example.com/page"', "https://example.com/page"),
            ("**https://example.com/page**", "https://example.com/page"),
        ],
    )
    def test_strips_what_ends_the_sentence(self, text: str, expected: str):
        assert extract(text).urls == [expected]

    def test_keeps_a_bracket_the_url_opened(self):
        url = "https://en.wikipedia.org/wiki/Mercury_(planet)"

        assert extract(f"Read {url}.").urls == [url]

    def test_reads_markdown_links(self):
        result = extract("See [the docs](https://example.com/docs) for details")

        assert result.urls == ["https://example.com/docs"]

    def test_reads_a_markdown_link_whose_text_is_another_url(self):
        result = extract("[https://a.example](https://b.example)")

        assert result.urls == ["https://a.example", "https://b.example"]

    def test_reads_angle_bracket_autolinks(self):
        assert extract("<https://example.com/page>").urls == ["https://example.com/page"]


class TestRejection:
    @pytest.mark.parametrize("url", ["ftp://files.example/report.pdf", "file:///etc/passwd", "ws://example.com/feed"])
    def test_reports_an_unsupported_scheme(self, url: str):
        result = extract(f"Open {url}")

        assert result.urls == []
        assert result.failures == [WebFetchFailure(url=url, reason=WebFetchFailureReason.UNSUPPORTED_URL)]

    @pytest.mark.parametrize(
        "url",
        [
            "https://",
            "https://example.com:99999/page",
            "https://example.com:port/page",
            "https://exa!mple.com",
            "https://example..com",
            f"https://{'a' * 64}.com",
        ],
    )
    def test_reports_a_malformed_url(self, url: str):
        result = extract(f"Open {url} now")

        assert result.urls == []
        assert result.failures == [WebFetchFailure(url=url, reason=WebFetchFailureReason.MALFORMED_URL)]

    def test_reports_failures_alongside_valid_urls(self):
        result = extract("Read https://example.com and ftp://files.example")

        assert result.urls == ["https://example.com"]
        assert [failure.reason for failure in result.failures] == [WebFetchFailureReason.UNSUPPORTED_URL]


class TestHostShapes:
    """Shape only: whether these hosts may be fetched is `UrlSafetyPolicy`'s call, not the extractor's."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://münchen.de/stadt",
            "https://my_service.example.com",
            "https://example.com./page",
            "https://example.com:8443/page",
            "http://192.168.1.10/admin",
            "http://[::1]:8080/",
            "http://litellm:4000/key/list",
        ],
    )
    def test_accepts_well_formed_hosts(self, url: str):
        assert extract(url).urls == [url]


class TestReferences:
    """Links referenced with `#` arrive as a list next to the message, and are sorted out the same way."""

    def test_keeps_a_reference_already_in_the_message_once(self):
        found = UrlExtractor.find("Summarize https://example.com/a")

        result = UrlExtractor.classify([*found, "https://example.com/a", "https://example.com/b"])

        assert result.urls == ["https://example.com/a", "https://example.com/b"]

    def test_reports_a_reference_that_is_no_url(self):
        result = UrlExtractor.classify(["not a url"])

        assert result.failures == [WebFetchFailure(url="not a url", reason=WebFetchFailureReason.MALFORMED_URL)]

    def test_ignores_whitespace_around_a_reference(self):
        assert UrlExtractor.classify(["  https://example.com/a "]).urls == ["https://example.com/a"]
