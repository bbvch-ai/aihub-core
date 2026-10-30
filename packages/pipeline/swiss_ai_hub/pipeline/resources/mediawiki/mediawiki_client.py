from collections.abc import Iterator
from typing import Annotated, Any
from urllib.parse import urlparse

from dlt.sources.helpers.requests.retry import Client
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth
from requests import Response, Session

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError

# A page deleted between the listing and the read answers with one of these instead of its content.
_GONE = {"nosuchpageid", "missingtitle"}
_DOWNLOAD_CHUNK_BYTES = 1 << 20


class MediaWikiClient:
    """Reads pages from a MediaWiki through its action API (``api.php``).

    Stateless apart from its session, and built per run from a database's decrypted configuration. A signed-in wiki
    knows the account by the session's cookies, which ``MediaWikiSignIn`` sets, or by an OAuth access token, which goes
    in through ``auth``. Both are added to a request only when it is prepared, after dlt has logged it. Every request
    runs through dlt's retrying session, which waits out 429 and 5xx answers, and none follows a redirect.
    """

    IDS_PER_QUERY = 50
    """How many ``pageids``/``revids``/``titles`` MediaWiki takes in one list from an account without
    ``apihighlimits``."""

    def __init__(
        self,
        base_url: Annotated[str, "The folder holding api.php and index.php, e.g. https://wiki.acme.ch"],
        access_token: Annotated[
            str | None, "OAuth 2 access token of an owner-only consumer; None to use cookies"
        ] = None,
        session: Annotated[Session | None, "HTTP session; a retrying dlt session when omitted"] = None,
    ):
        self.site_url = base_url.rstrip("/")
        self.api_url = f"{self.site_url}/api.php"
        self.session = session or Client(raise_for_status=False).session
        auth = BearerTokenAuth(token=access_token) if access_token else None
        self._rest = RESTClient(base_url=self.site_url, auth=auth, session=self.session)

    def query(self, params: Annotated[dict[str, Any], "Parameters of action=query"]) -> Iterator[dict[str, Any]]:
        """The ``query`` part of every answer, following MediaWiki's ``continue`` until it gives none.

        Paging never stops on a short answer, only on a missing ``continue``: a partial listing removes files of pages
        that still exist. A ``continue`` that repeats the previous one fails the read instead of looping.
        """
        request = {"action": "query", "format": "json", "formatversion": 2, **params}
        continuation: dict[str, Any] = {}
        while True:
            answer = self._get({**request, **continuation})
            yield answer.get("query") or {}
            following = answer.get("continue") or {}
            if not following:
                return
            if following == continuation:
                raise ValueError(f"MediaWiki at {self.site_url} repeated its continuation {following}.")
            continuation = following

    def site_info(self) -> dict[str, Any]:
        return next(self.query({"meta": "siteinfo", "siprop": "general|namespaces"}))

    def user_info(self) -> dict[str, Any]:
        """The account the session reads as; ``anon`` is set when it reads anonymously."""
        return next(self.query({"meta": "userinfo"}))["userinfo"]

    def token(self, kind: Annotated[str, "Token type, e.g. login"]) -> str:
        return next(self.query({"meta": "tokens", "type": kind}))["tokens"][f"{kind}token"]

    def pages(self, namespace: Annotated[int, "Namespace number"]) -> Iterator[list[dict[str, Any]]]:
        """Every page of the namespace except redirects, with its latest revision id and canonical URL, a batch at a
        time. A redirect has no content of its own; its target is synced under its own title."""
        for result in self.query(
            {
                "generator": "allpages",
                "gapnamespace": namespace,
                "gapfilterredir": "nonredirects",
                "gaplimit": "max",
                "prop": "info",
                "inprop": "url",
            }
        ):
            yield result.get("pages") or []

    def category_member_ids(self, category: Annotated[str, "Category name without its namespace prefix"]) -> set[int]:
        """IDs of the pages placed in the category, directly or through a template; not those of its subcategories."""
        return {
            member["pageid"]
            for result in self.query(
                {"list": "categorymembers", "cmtitle": f"Category:{category}", "cmprop": "ids", "cmlimit": "max"}
            )
            for member in result.get("categorymembers") or []
        }

    def categories(self, names: Annotated[list[str], "Category names without their namespace prefix"]) -> list[dict]:
        """The categories as pages, with their member counts: ``missing`` when the category has no page of its own,
        ``categoryinfo`` absent when nothing is in it either."""
        titles = "|".join(f"Category:{name}" for name in names)
        return next(self.query({"prop": "categoryinfo", "titles": titles})).get("pages") or []

    def parse(self, page_id: Annotated[int, "Page id"]) -> dict[str, Any] | None:
        """The page's current revision rendered as HTML, with its categories, or None when it was deleted since it was
        listed. Rendered HTML has every template expanded, which the stored wikitext does not."""
        try:
            answer = self._get(
                {
                    "action": "parse",
                    "pageid": page_id,
                    "prop": "text|categories|revid",
                    "disableeditsection": 1,
                    "disabletoc": 1,
                    "disablelimitreport": 1,
                    "format": "json",
                    "formatversion": 2,
                }
            )
        except MediaWikiRequestError as error:
            if error.code in _GONE:
                return None
            raise
        return answer["parse"]

    def first_revision_time(self, page_id: Annotated[int, "Page id"]) -> str | None:
        """When the page was created, from its oldest revision; None when it has none left."""
        result = next(
            self.query({"prop": "revisions", "pageids": page_id, "rvdir": "newer", "rvlimit": 1, "rvprop": "timestamp"})
        )
        pages = result.get("pages") or []
        revisions = (pages[0].get("revisions") if pages else None) or []
        return revisions[0]["timestamp"] if revisions else None

    def revision_times(self, revision_ids: Annotated[list[int], "Revision ids"]) -> dict[int, str]:
        """When each revision was saved, so a page's file says when it was last edited, which ``touched`` does not."""
        times: dict[int, str] = {}
        for start in range(0, len(revision_ids), self.IDS_PER_QUERY):
            batch = "|".join(str(revision) for revision in revision_ids[start : start + self.IDS_PER_QUERY])
            for result in self.query({"prop": "revisions", "revids": batch, "rvprop": "ids|timestamp"}):
                for page in result.get("pages") or []:
                    times.update({revision["revid"]: revision["timestamp"] for revision in page.get("revisions") or []})
        return times

    def files_used_by(self, page_ids: Annotated[list[int], "Ids of the pages whose files are wanted"]) -> list[dict]:
        """Every file the pages show or link to (``[[File:…]]``, ``[[Media:…]]``), once each, with its latest version's
        URL, size (an image's width and height too), checksum and MIME type in ``imageinfo``. A link to a file nobody uploaded has no ``imageinfo`` and
        is left out; ``imagerepository`` tells a file of this wiki from one of a shared repository."""
        files: dict[str, dict[str, Any]] = {}
        for start in range(0, len(page_ids), self.IDS_PER_QUERY):
            batch = "|".join(str(page_id) for page_id in page_ids[start : start + self.IDS_PER_QUERY])
            for result in self.query(
                {
                    "generator": "images",
                    "pageids": batch,
                    "gimlimit": "max",
                    "prop": "imageinfo",
                    "iiprop": "url|size|sha1|mime",
                }
            ):
                for file in result.get("pages") or []:
                    if file.get("imageinfo"):
                        files[file["title"]] = {**file, "imageinfo": file["imageinfo"][0]}
        return list(files.values())

    def download(
        self,
        url: Annotated[str, "A file's URL as imageinfo gave it"],
        max_bytes: Annotated[int, "Largest content to hold; a larger file is not read to the end"],
    ) -> bytes | None:
        """The file's content, read with the session's sign-in, or None when it is larger than ``max_bytes``.

        No redirect is followed, because the address guard checked this URL's host alone. A wiki behind a single
        sign-on gateway answers an expired session with its login page; HTML is therefore refused, since it would be
        stored and ingested as the document.
        """
        with self.session.get(
            url, stream=True, allow_redirects=False, hooks={"response": [self._raise_for_download_error]}
        ) as response:
            chunks: list[bytes] = []
            size = 0
            for chunk in response.iter_content(_DOWNLOAD_CHUNK_BYTES):
                size += len(chunk)
                if size > max_bytes:
                    return None
                chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _raise_for_download_error(response: Response, *args: Any, **kwargs: Any) -> None:
        if response.is_redirect or not response.ok:
            raise MediaWikiRequestError.from_response(response)
        if response.headers.get("Content-Type", "").startswith("text/html"):
            raise MediaWikiRequestError(
                f"MediaWiki answered {urlparse(response.url).path} with an HTML page instead of the file; the session "
                "may have expired.",
                response=response,
            )

    def raise_for_error(self, response: Response, *args: Any, **kwargs: Any) -> None:
        """A response hook, so the error is raised inside the retrying ``send`` and a 429 is waited out.

        MediaWiki answers an API error with status 200, and a single sign-on gateway in front of the wiki answers an
        expired session with an HTML page; both fail here instead of as a JSON decoding error later.
        """
        if response.is_redirect or not response.ok:
            raise MediaWikiRequestError.from_response(response)
        if (error := MediaWikiRequestError.api_error_of(response)) is not None:
            raise MediaWikiRequestError.from_api_error(response, error)
        if "json" not in response.headers.get("Content-Type", ""):
            content_type = response.headers.get("Content-Type") or "no content type"
            raise MediaWikiRequestError(
                f"MediaWiki at {self.site_url} answered with {content_type} instead of JSON; the wiki URL must be the "
                "folder holding api.php.",
                response=response,
            )

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self._rest.get(
            "api.php", params=params, hooks={"response": [self.raise_for_error]}, allow_redirects=False
        )
        return response.json()
