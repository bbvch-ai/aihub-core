from typing import Annotated
from urllib.parse import urlparse

import httpx

from swiss_ai_hub.core.infrastructure.searxng.searxng_engine import SearxngEngine
from swiss_ai_hub.core.infrastructure.searxng.searxng_result import SearxngResult
from swiss_ai_hub.core.infrastructure.searxng.searxng_safe_search import SearxngSafeSearch
from swiss_ai_hub.core.infrastructure.searxng.searxng_settings import SearxngSettings


class SearxngClient:
    """Searches the web through the platform's SearXNG, which fans one query out to its engines and merges the hits."""

    def __init__(self, settings: SearxngSettings | None = None) -> None:
        self._settings = settings or SearxngSettings()

    async def search(
        self,
        query: Annotated[str, "What to search for."],
        engines: Annotated[list[SearxngEngine] | None, "Engines to ask; none asks every engine SearXNG runs."] = None,
        language: Annotated[str, "Result language, a code like `de` or `auto`."] = "auto",
        safe_search: SearxngSafeSearch = SearxngSafeSearch.MODERATE,
        time_range: Annotated[str | None, "Only results from the last day, week, month or year."] = None,
        max_results: Annotated[int, "How many hits to keep, best first."] = 10,
    ) -> list[SearxngResult]:
        params: dict[str, str | int] = {
            "q": query,
            "format": "json",
            "language": language,
            "safesearch": safe_search.level,
        }
        if engines:
            params["engines"] = ",".join(engines)
        if time_range:
            params["time_range"] = time_range
        async with httpx.AsyncClient(base_url=self._settings.BASE_URL, timeout=self._settings.TIMEOUT) as http:
            response = await http.get("/search", params=params)
        response.raise_for_status()
        hits = response.json().get("results", [])
        return [SearxngResult.from_searxng(hit) for hit in hits if self._links_somewhere(hit.get("url"))][:max_results]

    @staticmethod
    def _links_somewhere(url: str | None) -> bool:
        """An engine whose page layout changed returns links SearXNG can no longer resolve, such as Brave's
        host-less `http:///go/v1/…` redirects; such a hit can be neither read nor opened, so it is left out."""
        parsed = urlparse(url or "")
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
