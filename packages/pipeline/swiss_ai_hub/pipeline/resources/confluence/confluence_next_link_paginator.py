from typing import Any, override
from urllib.parse import urlparse

from dlt.sources.helpers.rest_client.paginators import BaseNextUrlPaginator
from requests import Response


class ConfluenceNextLinkPaginator(BaseNextUrlPaginator):
    """Follows ``_links.next``, which Confluence gives relative to the site rather than to the host.

    On Cloud the site is ``…/wiki``, which joining the link onto the request URL would drop. Joining it onto the
    configured site instead also keeps every page on the host the address guard checked, whatever ``_links.base`` a
    response claims.
    """

    def __init__(self, site_url: str) -> None:
        super().__init__()
        self.site_url = site_url

    @override
    def update_state(self, response: Response, data: list[Any] | None = None) -> None:
        next_link = response.json().get("_links", {}).get("next")
        self._next_reference = self._on_site(next_link) if next_link else None

    def _on_site(self, next_link: str) -> str:
        """A server decides the link, so only a path below the site is followed. Appended to the site, anything else
        can move the request to another host: ``@elsewhere/…`` turns the site into user info, and ``.elsewhere/…`` or
        ``:8443/…`` extend its host or replace its port."""
        next_url = f"{self.site_url}{next_link}"
        site, joined = urlparse(self.site_url), urlparse(next_url)
        if not next_link.startswith("/") or next_link.startswith("//") or joined.netloc != site.netloc:
            raise ValueError(f"Confluence pointed to the next page outside the site: {next_link}")
        return next_url
