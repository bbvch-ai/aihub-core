import socket

import pytest
from swiss_ai_hub.core.events.agent import WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.url_safety_policy import UrlSafetyPolicy

PUBLIC_IP = "93.184.215.14"


@pytest.fixture(autouse=True)
def no_dns(monkeypatch: pytest.MonkeyPatch):
    """Agents sit on internal networks only, where Docker answers no outside name: a lookup here failed every link
    (#2186 on staging). Where a name leads is `browser-proxy`'s decision."""

    def refuse(*_: object, **__: object) -> list:
        raise AssertionError("UrlSafetyPolicy must not resolve names")

    monkeypatch.setattr(socket, "getaddrinfo", refuse)


class TestInternalNames:
    @pytest.mark.parametrize(
        "url",
        [
            "http://litellm:4000/key/list",
            "http://api:8000/agents",
            "http://localhost/",
            "http://LOCALHOST:3000/",
            "http://admin.localhost/",
            "http://printer.local/",
            "http://host.docker.internal/",
            "http://router.home.arpa/",
            "http://2130706433/",
        ],
    )
    def test_blocks_on_the_name_alone(self, url: str):
        """Refused before any request is sent; `browser-proxy` would refuse them too, but only after resolving."""
        assert UrlSafetyPolicy.check(url) == WebFetchFailureReason.BLOCKED_HOST


class TestIpLiterals:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://10.0.0.5/",
            "http://172.18.0.3:4000/",
            "http://192.168.1.10/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://100.64.0.1/",
            "http://0.0.0.0/",
            "http://224.0.0.1/",
            "http://[::1]/",
            "http://[fd00::1]/",
            "http://[fe80::1]/",
            "http://[::ffff:127.0.0.1]/",
            "http://[64:ff9b::7f00:1]/",
            "http://[2002:7f00:1::]/",
        ],
    )
    def test_blocks_non_public_addresses(self, url: str):
        assert UrlSafetyPolicy.check(url) == WebFetchFailureReason.BLOCKED_HOST

    @pytest.mark.parametrize("url", [f"http://{PUBLIC_IP}/", "http://[2606:4700:4700::1111]/"])
    def test_allows_public_addresses(self, url: str):
        assert UrlSafetyPolicy.check(url) is None


class TestNames:
    @pytest.mark.parametrize(
        "url",
        ["https://example.com/page", "https://evil.example/", "https://no-such-host.example/", "https://cdn.example/c"],
    )
    def test_leaves_where_a_name_leads_to_the_proxy(self, url: str):
        """A public-looking name can still point inside; `browser-proxy` refuses it for the address it connects to,
        which a lookup here could not bind, since the Playwright server resolves the name again."""
        assert UrlSafetyPolicy.check(url) is None


class TestSchemes:
    @pytest.mark.parametrize("url", ["data:text/plain,hello", "blob:https://example.com/uuid", "about:blank"])
    def test_allows_schemes_that_never_leave_the_browser(self, url: str):
        assert UrlSafetyPolicy.check(url) is None

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://files.example/x", "chrome://settings"])
    def test_blocks_other_schemes(self, url: str):
        """Subresource requests reach the policy too, and a page may ask for anything."""
        assert UrlSafetyPolicy.check(url) == WebFetchFailureReason.BLOCKED_HOST

    def test_checks_websockets_like_http(self):
        assert UrlSafetyPolicy.check("ws://litellm:4000/") == WebFetchFailureReason.BLOCKED_HOST


class TestAmbiguousUrls:
    """Python judges the host and Playwright fetches it, so a URL the two parse differently must never pass."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1\\@example.com/",
            "http://example.com\\.127.0.0.1/",
            "http://example.com@127.0.0.1/",
            "http://user:secret@example.com/",
            "http://exa mple.com/",
            "http://example.com\t/",
            "http://example.com/\x00",
            "http://example.com/\x7f",
            "http://faß.example/",
            "http://①②⑦.⓪.⓪.①/",
            "http://%31%32%37.0.0.1/",
        ],
    )
    def test_refuses(self, url: str):
        assert UrlSafetyPolicy.check(url) == WebFetchFailureReason.BLOCKED_HOST

    @pytest.mark.parametrize(
        "url",
        [
            "https://medium.com/@someone/post",
            "https://example.com/a\\b",
            "https://example.com/?q=a%20b",
            "https://xn--mnchen-3ya.de/stadt",
        ],
    )
    def test_allows_what_only_looks_alike_outside_the_host(self, url: str):
        """An `@`, backslash or escape outside the host changes nothing, and a Unicode domain reaches the policy
        as the browser reports it, in its ASCII form."""
        assert UrlSafetyPolicy.check(url) is None
