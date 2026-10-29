import asyncio

from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason
from swiss_ai_hub.core.infrastructure import PlaywrightSettings

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.page_content_converter import PageContentConverter
from swiss_ai_hub.agent.capabilities.web_fetch.request_guard import RequestGuard
from swiss_ai_hub.agent.capabilities.web_fetch.url_safety_policy import UrlSafetyPolicy

type FetchResult = FetchedWebPage | WebFetchFailure

MAX_CONCURRENT_PAGES = 4
MAX_NAVIGATION_REDIRECTS = 5
RENDER_SETTLE_SECONDS = 3.0
# The timeouts are staggered so the innermost ends a slow page first: the guard's own fetch times out and aborts
# cleanly, and only then would `goto` or the outer bound fire. Either of those closing the page while the guard's
# fetch is still running leaves Playwright futures unretrieved.
NAVIGATION_MARGIN_SECONDS = 1.0
BACKSTOP_MARGIN_SECONDS = NAVIGATION_MARGIN_SECONDS + RENDER_SETTLE_SECONDS + 2.0
NAVIGATION_ERROR_REASONS = {
    "net::ERR_BLOCKED_BY_CLIENT": WebFetchFailureReason.BLOCKED_HOST,
    "net::ERR_NAME_NOT_RESOLVED": WebFetchFailureReason.NOT_FOUND,
    "Download is starting": WebFetchFailureReason.UNSUPPORTED_CONTENT,
}


class WebPageFetcher:
    """Reads web pages through the platform's Playwright server; agents have no internet access of their own.

    The single place that knows the engine: replacing Playwright (e.g. with Firecrawl, #1605) changes this class
    and `RequestGuard`, and nothing that calls `fetch_all`.
    """

    @classmethod
    async def fetch_all(cls, urls: list[str], timeout_seconds: float, max_page_characters: int) -> list[FetchResult]:
        """Returns one result per URL, in the order given. Failing to reach the Playwright server itself raises:
        that is a platform fault, not something to report as an unreadable page."""
        if not urls:
            return []
        settings = PlaywrightSettings()
        policy = UrlSafetyPolicy()
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect(settings.WS_URL)
            try:
                context = await browser.new_context(service_workers="block", accept_downloads=False)
                await cls.refuse_unguarded_pages(context)
                results = await asyncio.gather(
                    *(
                        cls._fetch_limited(semaphore, context, policy, url, timeout_seconds, max_page_characters)
                        for url in urls
                    )
                )
            finally:
                await browser.close()
        return list(results)

    @staticmethod
    async def refuse_unguarded_pages(context: BrowserContext) -> None:
        """Refuses every request of a page the fetcher did not open, such as a popup the fetched page opens: its
        guard is routed on the page it reads, and a page's routes take precedence over the context's."""
        await context.route("**/*", RequestGuard.refuse_unguarded)
        await context.route_web_socket("**/*", RequestGuard.refuse_web_socket)

    @classmethod
    async def _fetch_limited(
        cls,
        semaphore: asyncio.Semaphore,
        context: BrowserContext,
        policy: UrlSafetyPolicy,
        url: str,
        timeout_seconds: float,
        max_page_characters: int,
    ) -> FetchResult:
        async with semaphore:
            try:
                async with asyncio.timeout(timeout_seconds + BACKSTOP_MARGIN_SECONDS):
                    return await cls._follow(context, policy, url, timeout_seconds, max_page_characters)
            except (TimeoutError, PlaywrightTimeoutError):
                return WebFetchFailure(url=url, reason=WebFetchFailureReason.TIMEOUT)

    @classmethod
    async def _follow(
        cls, context: BrowserContext, policy: UrlSafetyPolicy, url: str, timeout_seconds: float, max_characters: int
    ) -> FetchResult:
        target = url
        for _ in range(MAX_NAVIGATION_REDIRECTS + 1):
            result = await cls._visit(context, policy, url, target, timeout_seconds, max_characters)
            if not isinstance(result, str):
                return result
            target = result
        return WebFetchFailure(url=url, reason=WebFetchFailureReason.HTTP_ERROR)

    @classmethod
    async def _visit(
        cls,
        context: BrowserContext,
        policy: UrlSafetyPolicy,
        url: str,
        target: str,
        timeout_seconds: float,
        max_characters: int,
    ) -> FetchResult | str:
        """Opens `target` in a fresh page and returns the result, or the URL it redirects to.

        Fresh, because a page reused after an aborted navigation reports the next one as interrupted by Chrome's
        error page.
        """
        guard = RequestGuard(policy, timeout_seconds)
        page = await context.new_page()
        try:
            await page.route("**/*", guard.handle)
            await page.route_web_socket("**/*", RequestGuard.refuse_web_socket)
            navigation_failure = await cls._navigate(page, target, timeout_seconds)
            if guard.outcome.redirect_to is not None:
                return guard.outcome.redirect_to
            reason = guard.outcome.rejection or navigation_failure
            if reason is not None:
                return WebFetchFailure(url=url, reason=reason)
            await cls._settle(page)
            return await PageContentConverter.convert(
                url, page.url, await page.title(), await page.content(), max_characters
            )
        finally:
            # A guard still handling a request when the page closes would otherwise log a TargetClosedError.
            await page.unroute_all(behavior="ignoreErrors")
            await page.close()

    @classmethod
    async def _navigate(cls, page: Page, target: str, timeout_seconds: float) -> WebFetchFailureReason | None:
        try:
            await page.goto(
                target, wait_until="domcontentloaded", timeout=(timeout_seconds + NAVIGATION_MARGIN_SECONDS) * 1000
            )
        except PlaywrightTimeoutError:
            raise
        except PlaywrightError as error:
            return cls.reason_for_navigation_error(error)
        return None

    @staticmethod
    def reason_for_navigation_error(error: PlaywrightError) -> WebFetchFailureReason:
        """Unknown errors propagate: only a failure of the page itself is something to report to the user."""
        for marker, reason in NAVIGATION_ERROR_REASONS.items():
            if marker in error.message:
                return reason
        if "net::ERR_" in error.message:
            return WebFetchFailureReason.HTTP_ERROR
        raise error

    @staticmethod
    async def _settle(page: Page) -> None:
        """Gives script-rendered pages a moment to fill in after the HTML arrived."""
        try:
            await page.wait_for_load_state("networkidle", timeout=RENDER_SETTLE_SECONDS * 1000)
        except PlaywrightTimeoutError:
            # Pages with polling or analytics never go idle; what has rendered by now is what we read.
            return
