import ipaddress
import re
from urllib.parse import urlsplit

from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.extracted_urls import ExtractedUrls

# Any scheme, not only http(s), so that an ftp:// or file:// link is reported as unsupported instead of ignored.
# Brackets end a URL (markdown's `[text](url)`) except right after `://`, where they wrap an IPv6 host.
URL_CANDIDATE_PATTERN = re.compile(r"[a-z][a-z0-9+.\-]*://(?:\[[0-9a-f:.]+\])?[^\s<>\"'`\[\]]*", re.IGNORECASE)
SUPPORTED_SCHEMES = frozenset({"http", "https"})
TRAILING_PUNCTUATION = ".,;:!?'\"*_~"
CLOSING_TO_OPENING = {")": "(", "}": "{"}
HOSTNAME_LABEL_PATTERN = re.compile(r"^[a-z0-9_](?:[a-z0-9_\-]{0,61}[a-z0-9_])?$")
MAX_HOSTNAME_LENGTH = 253


class UrlExtractor:
    """Finds the links a user pasted into a message, so they can be fetched without the user marking them, and
    sorts out the ones that cannot be fetched at all before they reach the browser."""

    @classmethod
    def find(cls, text: str) -> list[str]:
        """Every link in the text, in message order and once each, without the punctuation that ends a sentence."""
        candidates = (cls._strip_trailing_punctuation(match.group()) for match in URL_CANDIDATE_PATTERN.finditer(text))
        return list(dict.fromkeys(candidates))

    @classmethod
    def classify(cls, urls: list[str]) -> ExtractedUrls:
        """The links worth fetching, and a failure for each malformed or unsupported one, the order kept."""
        result = ExtractedUrls()
        for url in dict.fromkeys(url.strip() for url in urls):
            reason = cls._rejection_reason(url)
            if reason is None:
                result.urls.append(url)
            else:
                result.failures.append(WebFetchFailure(url=url, reason=reason))
        return result

    @staticmethod
    def _strip_trailing_punctuation(url: str) -> str:
        """Drops what ends the sentence around a URL, keeping a closing bracket the URL itself opened, as in
        Wikipedia's `/wiki/Mercury_(planet)`."""
        while url:
            last = url[-1]
            opening = CLOSING_TO_OPENING.get(last)
            if last in TRAILING_PUNCTUATION or (opening and url.count(opening) < url.count(last)):
                url = url[:-1]
            else:
                break
        return url

    @classmethod
    def _rejection_reason(cls, url: str) -> WebFetchFailureReason | None:
        try:
            parts = urlsplit(url)
            parts.port  # urlsplit accepts any port text; only reading it raises for a non-numeric or out-of-range one
        except ValueError:
            return WebFetchFailureReason.MALFORMED_URL
        if not parts.scheme:
            return WebFetchFailureReason.MALFORMED_URL
        if parts.scheme.lower() not in SUPPORTED_SCHEMES:
            return WebFetchFailureReason.UNSUPPORTED_URL
        if not parts.hostname or not cls._is_valid_host(parts.hostname):
            return WebFetchFailureReason.MALFORMED_URL
        return None

    @staticmethod
    def _is_valid_host(hostname: str) -> bool:
        """Checks shape only; whether the host may be fetched at all is `UrlSafetyPolicy`'s decision."""
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass
        try:
            ascii_hostname = hostname.rstrip(".").encode("idna").decode("ascii")
        except UnicodeError:
            return False
        labels = ascii_hostname.split(".")
        return len(ascii_hostname) <= MAX_HOSTNAME_LENGTH and all(
            HOSTNAME_LABEL_PATTERN.match(label) for label in labels
        )
