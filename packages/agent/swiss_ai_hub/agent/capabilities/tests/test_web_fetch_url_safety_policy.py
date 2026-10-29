import ipaddress
import socket

import pytest
from swiss_ai_hub.core.events.agent import WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.url_safety_policy import UrlSafetyPolicy

PUBLIC_IP = "93.184.215.14"


@pytest.fixture
def resolve_to(monkeypatch: pytest.MonkeyPatch):
    """Replaces DNS so no test depends on the network; records every lookup to prove the cache works."""
    lookups: list[str] = []

    def configure(*addresses: str):
        async def fake_resolve(hostname: str) -> list:
            lookups.append(hostname)
            if not addresses:
                raise socket.gaierror(socket.EAI_NONAME, "Name or service not known")
            return [ipaddress.ip_address(address) for address in addresses]

        monkeypatch.setattr(UrlSafetyPolicy, "_resolve", staticmethod(fake_resolve))
        return lookups

    return configure


@pytest.mark.asyncio
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
    async def test_blocks_without_asking_dns(self, url: str, resolve_to):
        """Blocked on the name alone, so a resolver that knows Docker's service names is never consulted."""
        lookups = resolve_to(PUBLIC_IP)

        assert await UrlSafetyPolicy().check(url) == WebFetchFailureReason.BLOCKED_HOST
        assert lookups == []


@pytest.mark.asyncio
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
    async def test_blocks_non_public_addresses(self, url: str):
        assert await UrlSafetyPolicy().check(url) == WebFetchFailureReason.BLOCKED_HOST

    @pytest.mark.parametrize("url", [f"http://{PUBLIC_IP}/", "http://[2606:4700:4700::1111]/"])
    async def test_allows_public_addresses(self, url: str):
        assert await UrlSafetyPolicy().check(url) is None


@pytest.mark.asyncio
class TestResolvedNames:
    async def test_allows_a_name_resolving_to_a_public_address(self, resolve_to):
        resolve_to(PUBLIC_IP)

        assert await UrlSafetyPolicy().check("https://example.com/page") is None

    async def test_blocks_a_public_looking_name_resolving_inside(self, resolve_to):
        """A public domain can point anywhere, including 127.0.0.1; the name alone proves nothing."""
        resolve_to("127.0.0.1")

        assert await UrlSafetyPolicy().check("https://evil.example/") == WebFetchFailureReason.BLOCKED_HOST

    async def test_blocks_when_any_resolved_address_is_internal(self, resolve_to):
        """The browser may pick any of the records, so one internal record is enough to refuse."""
        resolve_to(PUBLIC_IP, "10.0.0.5")

        assert await UrlSafetyPolicy().check("https://mixed.example/") == WebFetchFailureReason.BLOCKED_HOST

    async def test_reports_an_unresolvable_name_as_not_found(self, resolve_to):
        resolve_to()

        assert await UrlSafetyPolicy().check("https://no-such-host.example/") == WebFetchFailureReason.NOT_FOUND

    async def test_resolves_each_host_once_per_instance(self, resolve_to):
        """Every image and script on a page passes through the policy; one lookup per host keeps that cheap."""
        lookups = resolve_to(PUBLIC_IP)
        policy = UrlSafetyPolicy()

        await policy.check("https://example.com/a")
        await policy.check("https://example.com/b.js")
        await policy.check("https://cdn.example.com/c.png")

        assert lookups == ["example.com", "cdn.example.com"]


@pytest.mark.asyncio
class TestSchemes:
    @pytest.mark.parametrize("url", ["data:text/plain,hello", "blob:https://example.com/uuid", "about:blank"])
    async def test_allows_schemes_that_never_leave_the_browser(self, url: str):
        assert await UrlSafetyPolicy().check(url) is None

    @pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://files.example/x", "chrome://settings"])
    async def test_blocks_other_schemes(self, url: str):
        """Subresource requests reach the policy too, and a page may ask for anything."""
        assert await UrlSafetyPolicy().check(url) == WebFetchFailureReason.BLOCKED_HOST

    async def test_checks_websockets_like_http(self, resolve_to):
        assert await UrlSafetyPolicy().check("ws://litellm:4000/") == WebFetchFailureReason.BLOCKED_HOST


@pytest.mark.asyncio
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
    async def test_refuses_without_asking_dns(self, url: str, resolve_to):
        lookups = resolve_to(PUBLIC_IP)

        assert await UrlSafetyPolicy().check(url) == WebFetchFailureReason.BLOCKED_HOST
        assert lookups == []

    @pytest.mark.parametrize(
        "url",
        [
            "https://medium.com/@someone/post",
            "https://example.com/a\\b",
            "https://example.com/?q=a%20b",
            "https://xn--mnchen-3ya.de/stadt",
        ],
    )
    async def test_allows_what_only_looks_alike_outside_the_host(self, url: str, resolve_to):
        """An `@`, backslash or escape outside the host changes nothing, and a Unicode domain reaches the policy
        as the browser reports it, in its ASCII form."""
        resolve_to(PUBLIC_IP)

        assert await UrlSafetyPolicy().check(url) is None
