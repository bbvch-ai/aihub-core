from typing import Any

import pytest
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from swiss_ai_hub.core.events.agent import WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.request_guard import RequestGuard


class FakeResponse:
    def __init__(self, status: int = 200, headers: dict[str, str] | None = None):
        self.status = status
        self.headers = {"content-type": "text/html; charset=utf-8"} if headers is None else headers


class FakeFrame:
    def __init__(self, parent_frame: "FakeFrame | None" = None):
        self.parent_frame = parent_frame


class FakeRequest:
    def __init__(self, url: str, resource_type: str, navigation: bool, frame: FakeFrame):
        self.url = url
        self.resource_type = resource_type
        self.frame = frame
        self._navigation = navigation

    def is_navigation_request(self) -> bool:
        return self._navigation


class FakeRoute:
    """Plays the server: `responses` maps each URL the guard fetches to what that URL answers."""

    def __init__(self, request: FakeRequest, responses: dict[str, FakeResponse | Exception]):
        self.request = request
        self.responses = responses
        self.fetched: list[str] = []
        self.aborted_with: str | None = None
        self.fulfilled_with: FakeResponse | None = None

    async def fetch(self, url: str | None = None, **_: Any) -> FakeResponse:
        target = url or self.request.url
        self.fetched.append(target)
        response = self.responses[target]
        if isinstance(response, Exception):
            raise response
        return response

    async def abort(self, error_code: str) -> None:
        self.aborted_with = error_code

    async def fulfill(self, response: FakeResponse) -> None:
        self.fulfilled_with = response


def document(url: str, **responses: FakeResponse | Exception) -> FakeRoute:
    return FakeRoute(FakeRequest(url, "document", True, FakeFrame()), dict(responses) or {url: FakeResponse()})


def subresource(url: str, responses: dict[str, FakeResponse | Exception], resource_type: str = "script") -> FakeRoute:
    return FakeRoute(FakeRequest(url, resource_type, False, FakeFrame()), responses)


def redirect(location: str, status: int = 302) -> FakeResponse:
    return FakeResponse(status, {"location": location})


def proxy_refusal(status: int, error_code: str) -> FakeResponse:
    """What `browser-proxy` (Squid) answers in the site's place: an empty page and the reason in a header."""
    return FakeResponse(status, {"content-type": "text/html;charset=utf-8", "x-squid-error": f"{error_code} 0"})


@pytest.fixture
def guard() -> RequestGuard:
    return RequestGuard(timeout_seconds=5)


class TestReasonForResponse:
    @pytest.mark.parametrize(
        ("status", "reason"),
        [
            (404, WebFetchFailureReason.NOT_FOUND),
            (410, WebFetchFailureReason.NOT_FOUND),
            (401, WebFetchFailureReason.ACCESS_DENIED),
            (403, WebFetchFailureReason.ACCESS_DENIED),
            (429, WebFetchFailureReason.ACCESS_DENIED),
            (451, WebFetchFailureReason.ACCESS_DENIED),
            (400, WebFetchFailureReason.HTTP_ERROR),
            (500, WebFetchFailureReason.HTTP_ERROR),
            (503, WebFetchFailureReason.HTTP_ERROR),
        ],
    )
    def test_maps_error_statuses(self, status: int, reason: WebFetchFailureReason):
        """A server failure is not the user being refused: only 401/403/429/451 say access was denied."""
        assert RequestGuard.reason_for_response(status, "text/html") == reason

    @pytest.mark.parametrize(
        "content_type",
        ["text/html", "text/html; charset=utf-8", "TEXT/HTML", "application/xhtml+xml", "text/plain", ""],
    )
    def test_accepts_readable_content(self, content_type: str):
        """A missing content type is let through: extraction then decides whether anything readable came back."""
        assert RequestGuard.reason_for_response(200, content_type) is None

    @pytest.mark.parametrize("content_type", ["application/pdf", "image/png", "application/zip", "application/json"])
    def test_refuses_other_content(self, content_type: str):
        assert RequestGuard.reason_for_response(200, content_type) == WebFetchFailureReason.UNSUPPORTED_CONTENT


@pytest.mark.asyncio
class TestMainDocument:
    async def test_hands_a_readable_page_to_the_browser(self, guard: RequestGuard):
        route = document("https://example.com/")

        await guard.handle(route)

        assert route.fulfilled_with is not None
        assert guard.outcome.rejection is None

    async def test_never_hands_a_redirect_to_the_browser(self, guard: RequestGuard):
        """The browser would follow it unrouted, so the fetcher opens the target as a new, checked page instead."""
        route = document("https://short.example/x", **{"https://short.example/x": redirect("/landing")})

        await guard.handle(route)

        assert route.fulfilled_with is None
        assert route.aborted_with is not None
        assert guard.outcome.redirect_to == "https://short.example/landing"

    @pytest.mark.parametrize(
        ("response", "reason"),
        [
            (FakeResponse(404), WebFetchFailureReason.NOT_FOUND),
            (FakeResponse(200, {"content-type": "application/pdf"}), WebFetchFailureReason.UNSUPPORTED_CONTENT),
        ],
    )
    async def test_records_why_it_refused(self, guard: RequestGuard, response: FakeResponse, reason):
        route = document("https://example.com/doc", **{"https://example.com/doc": response})

        await guard.handle(route)

        assert route.fulfilled_with is None
        assert guard.outcome.rejection == reason

    @pytest.mark.parametrize(
        ("response", "reason"),
        [
            (proxy_refusal(403, "ERR_ACCESS_DENIED"), WebFetchFailureReason.BLOCKED_HOST),
            (proxy_refusal(503, "ERR_DNS_FAIL"), WebFetchFailureReason.NOT_FOUND),
            (proxy_refusal(503, "ERR_CONNECT_FAIL"), WebFetchFailureReason.HTTP_ERROR),
            (FakeResponse(403, {"content-type": "text/html"}), WebFetchFailureReason.ACCESS_DENIED),
        ],
    )
    async def test_tells_the_proxy_refusing_apart_from_the_site(self, guard: RequestGuard, response, reason):
        """A name that resolves inside passes the policy, and only the proxy sees where it leads: its 403 means a
        blocked host, not a site that denied access."""
        route = document("https://inside.example/", **{"https://inside.example/": response})

        await guard.handle(route)

        assert route.fulfilled_with is None
        assert guard.outcome.rejection == reason

    async def test_refuses_a_blocked_host_without_fetching(self, guard: RequestGuard):
        route = document("http://litellm:4000/key/list")

        await guard.handle(route)

        assert route.fetched == []
        assert guard.outcome.rejection == WebFetchFailureReason.BLOCKED_HOST

    @pytest.mark.parametrize(
        ("error", "reason"),
        [
            (PlaywrightTimeoutError("Timeout 5000ms exceeded"), WebFetchFailureReason.TIMEOUT),
            (PlaywrightError("connect ECONNREFUSED"), WebFetchFailureReason.HTTP_ERROR),
        ],
    )
    async def test_resolves_the_route_when_fetching_fails(self, guard: RequestGuard, error: Exception, reason):
        """An unresolved route would leave the page waiting until the whole fetch timed out."""
        route = document("https://example.com/", **{"https://example.com/": error})

        await guard.handle(route)

        assert route.aborted_with is not None
        assert guard.outcome.rejection == reason


@pytest.mark.asyncio
class TestSubresources:
    async def test_follows_redirects_itself_checking_every_hop(self, guard: RequestGuard):
        route = subresource(
            "https://cdn.example/a.js",
            {
                "https://cdn.example/a.js": redirect("https://cdn.example/b.js"),
                "https://cdn.example/b.js": FakeResponse(200, {"content-type": "text/javascript"}),
            },
        )

        await guard.handle(route)

        assert route.fetched == ["https://cdn.example/a.js", "https://cdn.example/b.js"]
        assert route.fulfilled_with is not None

    async def test_refuses_a_redirect_into_the_platform(self, guard: RequestGuard):
        """public → public → internal: the chain only turns internal at the second hop."""
        route = subresource(
            "https://cdn.example/a.js",
            {
                "https://cdn.example/a.js": redirect("https://cdn.example/b.js"),
                "https://cdn.example/b.js": redirect("http://litellm:4000/key/list"),
            },
        )

        await guard.handle(route)

        assert "http://litellm:4000/key/list" not in route.fetched
        assert route.aborted_with == "blockedbyclient"

    async def test_refuses_a_redirect_python_and_the_browser_read_differently(self, guard: RequestGuard):
        """Python reads this as cdn.example; Playwright, which would fetch it, as 127.0.0.1."""
        target = "http://127.0.0.1\\@cdn.example/x.js"
        route = subresource("https://cdn.example/a.js", {"https://cdn.example/a.js": redirect(target)})

        await guard.handle(route)

        assert route.fetched == ["https://cdn.example/a.js"]
        assert route.aborted_with == "blockedbyclient"

    async def test_gives_up_on_an_endless_redirect_loop(self, guard: RequestGuard):
        route = subresource("https://loop.example/a", {"https://loop.example/a": redirect("https://loop.example/a")})

        await guard.handle(route)

        assert route.aborted_with == "failed"

    @pytest.mark.parametrize("resource_type", ["image", "media", "font"])
    async def test_skips_what_carries_no_text(self, guard: RequestGuard, resource_type: str):
        route = subresource("https://cdn.example/x", {}, resource_type=resource_type)

        await guard.handle(route)

        assert route.fetched == []
        assert route.aborted_with == "blockedbyclient"

    async def test_does_not_blame_the_page_for_a_refused_subresource(self, guard: RequestGuard):
        route = subresource("http://litellm:4000/tracker.js", {})

        await guard.handle(route)

        assert route.aborted_with == "blockedbyclient"
        assert guard.outcome.rejection is None
