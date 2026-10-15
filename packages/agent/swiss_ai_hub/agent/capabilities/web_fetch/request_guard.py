from urllib.parse import urljoin

from playwright.async_api import APIResponse, Request, Route, WebSocketRoute
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from swiss_ai_hub.core.events.agent import WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.navigation_outcome import NavigationOutcome
from swiss_ai_hub.agent.capabilities.web_fetch.url_safety_policy import UrlSafetyPolicy

READABLE_CONTENT_TYPES = frozenset({"", "text/html", "application/xhtml+xml", "text/plain"})
SKIPPED_RESOURCE_TYPES = frozenset({"image", "media", "font"})
MAX_SUBRESOURCE_REDIRECTS = 5
STATUS_REASONS = {
    401: WebFetchFailureReason.ACCESS_DENIED,
    403: WebFetchFailureReason.ACCESS_DENIED,
    404: WebFetchFailureReason.NOT_FOUND,
    410: WebFetchFailureReason.NOT_FOUND,
    429: WebFetchFailureReason.ACCESS_DENIED,
    451: WebFetchFailureReason.ACCESS_DENIED,
}


class RequestGuard:
    """Performs every request of one page itself, so the browser only ever receives a response that was checked.

    Playwright routes the first request of a navigation and lets the browser follow redirects unseen, even when
    the redirect was handed over by `route.fulfill` (verified against the 1.60 server). A redirect therefore never
    reaches the browser: the main document's target is recorded for the fetcher to open as a new, routed page,
    and a subresource's hops are followed here, each checked by the policy.
    """

    def __init__(self, policy: UrlSafetyPolicy, timeout_seconds: float) -> None:
        self.outcome = NavigationOutcome()
        self._policy = policy
        self._timeout_ms = timeout_seconds * 1000

    async def handle(self, route: Route) -> None:
        request = route.request
        if request.resource_type in SKIPPED_RESOURCE_TYPES:
            await route.abort("blockedbyclient")
            return
        reason = await self._policy.check(request.url)
        if reason is not None:
            await self._refuse(route, reason)
            return
        try:
            if self._is_main_document(request):
                await self._handle_document(route)
            else:
                await self._handle_subresource(route)
        except PlaywrightTimeoutError:
            await self._refuse(route, WebFetchFailureReason.TIMEOUT)
        except PlaywrightError:
            # Every route must be resolved, or the page waits on it until the fetch times out.
            await self._refuse(route, WebFetchFailureReason.HTTP_ERROR)

    @staticmethod
    async def refuse_web_socket(web_socket: WebSocketRoute) -> None:
        """Never connected to a server, so a page's script cannot open a socket into the platform either."""
        await web_socket.close()

    @staticmethod
    async def refuse_unguarded(route: Route) -> None:
        """A request no guard checked is never sent."""
        await route.abort("blockedbyclient")

    @staticmethod
    def reason_for_response(status: int, content_type: str) -> WebFetchFailureReason | None:
        if status >= 400:
            return STATUS_REASONS.get(status, WebFetchFailureReason.HTTP_ERROR)
        if content_type.split(";")[0].strip().lower() not in READABLE_CONTENT_TYPES:
            return WebFetchFailureReason.UNSUPPORTED_CONTENT
        return None

    @staticmethod
    def redirect_location(url: str, response: APIResponse) -> str | None:
        location = response.headers.get("location")
        if 300 <= response.status < 400 and location:
            return urljoin(url, location)
        return None

    @staticmethod
    def _is_main_document(request: Request) -> bool:
        return request.is_navigation_request() and request.frame.parent_frame is None

    async def _refuse(self, route: Route, reason: WebFetchFailureReason) -> None:
        if self._is_main_document(route.request):
            self.outcome.rejection = reason
        await route.abort("blockedbyclient")

    async def _handle_document(self, route: Route) -> None:
        response = await route.fetch(max_redirects=0, timeout=self._timeout_ms)
        location = self.redirect_location(route.request.url, response)
        if location is not None:
            self.outcome.redirect_to = location
            await route.abort("aborted")
            return
        reason = self.reason_for_response(response.status, response.headers.get("content-type", ""))
        if reason is not None:
            await self._refuse(route, reason)
            return
        await route.fulfill(response=response)

    async def _handle_subresource(self, route: Route) -> None:
        url = route.request.url
        for _ in range(MAX_SUBRESOURCE_REDIRECTS + 1):
            response = await route.fetch(url=url, max_redirects=0, timeout=self._timeout_ms)
            location = self.redirect_location(url, response)
            if location is None:
                await route.fulfill(response=response)
                return
            if await self._policy.check(location) is not None:
                await route.abort("blockedbyclient")
                return
            url = location
        await route.abort("failed")
