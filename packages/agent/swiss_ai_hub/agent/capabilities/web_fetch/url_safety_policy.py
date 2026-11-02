import ipaddress
from urllib.parse import urlsplit

from swiss_ai_hub.core.events.agent import WebFetchFailureReason

type IpAddress = ipaddress.IPv4Address | ipaddress.IPv6Address

NETWORK_SCHEMES = frozenset({"http", "https", "ws", "wss"})
LOCAL_ONLY_SCHEMES = frozenset({"data", "blob", "about"})
BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal", ".home.arpa")
NAT64_PREFIX = ipaddress.IPv6Network("64:ff9b::/96")
SPACE_CODE_POINT = 0x20
DELETE_CODE_POINT = 0x7F
AMBIGUOUS_NETLOC_CHARACTERS = ("\\", "@", "%")


class UrlSafetyPolicy:
    """Refuses what the URL alone shows must not leave the platform: internal names, non-public addresses, and URLs
    Python and the browser could read as different hosts. Applied to the pasted URL and to every request the page
    makes, redirects included.

    Where a name leads is not judged here. Agents have no DNS for outside names (they sit on internal networks
    only), and the Playwright server would resolve the name again anyway. `browser-proxy`, the browser's only way
    out, refuses non-public addresses for the address it actually connects to.
    """

    @classmethod
    def check(cls, url: str) -> WebFetchFailureReason | None:
        """Returns why the URL must not be requested, or None when it may be."""
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme in LOCAL_ONLY_SCHEMES:
            return None
        if scheme not in NETWORK_SCHEMES or cls._is_ambiguous(url, parts.netloc):
            return WebFetchFailureReason.BLOCKED_HOST
        if not parts.hostname:
            return WebFetchFailureReason.MALFORMED_URL
        return cls._judge_host(parts.hostname)

    @staticmethod
    def _is_ambiguous(url: str, netloc: str) -> bool:
        """A URL Python and the browser could read as different hosts is refused rather than judged by the wrong
        parser. Redirect targets are checked as Python joined them and then fetched by Playwright, which follows
        the URL standard: `http://127.0.0.1\\@example.com/` is example.com to `urlsplit` and 127.0.0.1 to it.

        A host must be ASCII and unescaped: Python resolves Unicode names by IDNA 2003 and the browser by UTS 46,
        which map `faß.example` to different domains, and only the browser decodes a `%`-escaped host. Every
        request the browser itself reports already carries its host in ASCII, so only a raw redirect target can
        fail this.
        """
        return (
            not netloc.isascii()
            or any(character in netloc for character in AMBIGUOUS_NETLOC_CHARACTERS)
            or any(ord(character) <= SPACE_CODE_POINT or ord(character) == DELETE_CODE_POINT for character in url)
        )

    @classmethod
    def _judge_host(cls, hostname: str) -> WebFetchFailureReason | None:
        literal = cls._as_ip_address(hostname)
        if literal is not None:
            return None if cls._is_public(literal) else WebFetchFailureReason.BLOCKED_HOST
        if cls._is_internal_name(hostname):
            return WebFetchFailureReason.BLOCKED_HOST
        return None

    @staticmethod
    def _is_internal_name(hostname: str) -> bool:
        """Docker service names (`litellm`, `api`) are single labels; a public site always has a dot."""
        name = hostname.rstrip(".").lower()
        return "." not in name or name == "localhost" or name.endswith(BLOCKED_HOST_SUFFIXES)

    @staticmethod
    def _as_ip_address(hostname: str) -> IpAddress | None:
        try:
            return ipaddress.ip_address(hostname)
        except ValueError:
            return None

    @classmethod
    def _is_public(cls, address: IpAddress) -> bool:
        embedded = cls._embedded_ipv4(address)
        if embedded is not None:
            return cls._is_public(embedded)
        return address.is_global and not address.is_multicast

    @staticmethod
    def _embedded_ipv4(address: IpAddress) -> ipaddress.IPv4Address | None:
        """IPv6 forms that carry an IPv4 address report `is_global` for the wrapper, not for what they reach:
        `64:ff9b::7f00:1` is NAT64 for 127.0.0.1."""
        if not isinstance(address, ipaddress.IPv6Address):
            return None
        if address.ipv4_mapped is not None:
            return address.ipv4_mapped
        if address.sixtofour is not None:
            return address.sixtofour
        if address in NAT64_PREFIX:
            return ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        return None
