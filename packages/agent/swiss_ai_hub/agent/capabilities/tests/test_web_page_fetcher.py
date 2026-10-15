import os

import pytest
from playwright.async_api import Error as PlaywrightError
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.web_page_fetcher import WebPageFetcher


class TestReasonForNavigationError:
    @pytest.mark.parametrize(
        ("message", "reason"),
        [
            ("Page.goto: net::ERR_BLOCKED_BY_CLIENT at https://x.example", WebFetchFailureReason.BLOCKED_HOST),
            ("Page.goto: net::ERR_NAME_NOT_RESOLVED at https://x.example", WebFetchFailureReason.NOT_FOUND),
            ("Page.goto: Download is starting", WebFetchFailureReason.UNSUPPORTED_CONTENT),
            ("Page.goto: net::ERR_CONNECTION_REFUSED at https://x.example", WebFetchFailureReason.HTTP_ERROR),
            ("Page.goto: net::ERR_CERT_DATE_INVALID at https://x.example", WebFetchFailureReason.HTTP_ERROR),
        ],
    )
    def test_maps_what_the_page_itself_did(self, message: str, reason: WebFetchFailureReason):
        assert WebPageFetcher.reason_for_navigation_error(PlaywrightError(message)) == reason

    def test_raises_what_is_not_about_the_page(self):
        """A closed browser is a platform fault; reporting it as an unreadable page would hide it."""
        error = PlaywrightError("Target page, context or browser has been closed")

        with pytest.raises(PlaywrightError):
            WebPageFetcher.reason_for_navigation_error(error)


@pytest.mark.asyncio
async def test_fetches_nothing_for_no_urls():
    """No browser connection is opened, so a message without links costs nothing."""
    assert await WebPageFetcher.fetch_all([], timeout_seconds=5, max_page_characters=1000) == []


@pytest.mark.integration
@pytest.mark.flaky
@pytest.mark.asyncio
async def test_reads_real_pages_through_the_playwright_server(monkeypatch: pytest.MonkeyPatch):
    """Needs the dev stack's Playwright server and internet access. Marked flaky because it depends on third-party
    sites, which CI must not; run it locally after changing the fetcher or `RequestGuard`."""
    monkeypatch.setenv("PLAYWRIGHT_WS_URL", os.environ.get("PLAYWRIGHT_WS_URL", "ws://localhost:3036"))
    urls = [
        "https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com%2F",
        "https://httpbin.org/redirect-to?url=http%3A%2F%2Flocalhost%3A3000%2F",
        "https://httpbin.org/status/404",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "http://litellm:4000/",
    ]

    results = await WebPageFetcher.fetch_all(urls, timeout_seconds=15, max_page_characters=4000)

    assert isinstance(results[0], FetchedWebPage)
    assert results[0].title == "Example Domain"
    assert results[1:] == [
        WebFetchFailure(url=urls[1], reason=WebFetchFailureReason.BLOCKED_HOST),
        WebFetchFailure(url=urls[2], reason=WebFetchFailureReason.NOT_FOUND),
        WebFetchFailure(url=urls[3], reason=WebFetchFailureReason.UNSUPPORTED_CONTENT),
        WebFetchFailure(url=urls[4], reason=WebFetchFailureReason.BLOCKED_HOST),
    ]
