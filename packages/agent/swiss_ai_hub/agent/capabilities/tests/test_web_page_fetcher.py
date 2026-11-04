import os

import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.web_page_fetcher import WebPageFetcher

POPUP_URL = "http://popup.example/opened"
POPUP_PAGE = f"<script>window.open('{POPUP_URL}')</script>"


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
async def test_a_page_the_fetched_page_opens_sends_nothing():
    """Needs the dev stack's Playwright server, which CI does not run. The fetched page is checked by its own
    routes; a popup it opens has none, so the context refuses that page's requests instead."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect(os.environ.get("PLAYWRIGHT_WS_URL", "ws://localhost:3036"))
        try:
            context = await browser.new_context()
            await WebPageFetcher.refuse_unguarded_pages(context)
            page = await context.new_page()
            await page.route("**/*", lambda route: route.fulfill(content_type="text/html", body=POPUP_PAGE))

            async with context.expect_event(
                "requestfailed", predicate=lambda request: request.url == POPUP_URL, timeout=10_000
            ) as failed:
                await page.goto("http://page.example/")

            assert (await failed.value).failure == "net::ERR_BLOCKED_BY_CLIENT"
        finally:
            await browser.close()


@pytest.mark.integration
@pytest.mark.flaky
@pytest.mark.asyncio
async def test_reads_real_pages_through_the_playwright_server(monkeypatch: pytest.MonkeyPatch):
    """Needs the dev stack's Playwright server and `browser-proxy`, and internet access. Marked flaky because it
    depends on third-party sites, which CI must not; run it locally after changing the fetcher, `RequestGuard` or the
    proxy. `127.0.0.1.nip.io` is a public name for a private address, so only the proxy can refuse it."""
    monkeypatch.setenv("PLAYWRIGHT_WS_URL", os.environ.get("PLAYWRIGHT_WS_URL", "ws://localhost:3036"))
    urls = [
        "https://httpbin.org/redirect-to?url=https%3A%2F%2Fexample.com%2F",
        "https://httpbin.org/redirect-to?url=http%3A%2F%2Flocalhost%3A3000%2F",
        "https://httpbin.org/status/404",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "http://litellm:4000/",
        "http://127.0.0.1.nip.io:3000/",
    ]

    results = await WebPageFetcher.fetch_all(urls, timeout_seconds=15, max_page_characters=4000)

    assert isinstance(results[0], FetchedWebPage)
    assert results[0].title == "Example Domain"
    assert results[1:] == [
        WebFetchFailure(url=urls[1], reason=WebFetchFailureReason.BLOCKED_HOST),
        WebFetchFailure(url=urls[2], reason=WebFetchFailureReason.NOT_FOUND),
        WebFetchFailure(url=urls[3], reason=WebFetchFailureReason.UNSUPPORTED_CONTENT),
        WebFetchFailure(url=urls[4], reason=WebFetchFailureReason.BLOCKED_HOST),
        WebFetchFailure(url=urls[5], reason=WebFetchFailureReason.BLOCKED_HOST),
    ]
