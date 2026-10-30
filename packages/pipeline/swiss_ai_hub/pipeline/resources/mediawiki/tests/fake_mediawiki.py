"""An in-memory MediaWiki answering the action API calls ``MediaWikiClient`` makes, and the login page
``MediaWikiSignIn`` fills in.

It is served through a ``requests`` transport adapter mounted on a real dlt retrying session, so the client's retry
and error handling run exactly as in production. Listings come a few entries at a time with a ``continue``, as
MediaWiki returns them to an account without ``apihighlimits``. The fake holds one session: signing in, through either
method, makes every later request read as the account.
"""

import hashlib
import json
import mimetypes
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import pytest
from dlt.sources.helpers.requests.retry import Client
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter

SITE = "https://wiki.acme.test"
NAMESPACES = {0: "", 1: "Talk", 4: "Project", 6: "File", 10: "Template", 14: "Category", 100: "Process"}
_REASONS = {
    200: "OK",
    302: "Found",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    429: "Too Many Requests",
    500: "Internal Server Error",
}

type Answer = tuple[int, dict[str, Any] | str | bytes, dict[str, str]]


class FakeMediaWikiTransport(BaseAdapter):
    def __init__(self, wiki: "FakeMediaWiki"):
        super().__init__()
        self.wiki = wiki

    def send(self, request: PreparedRequest, *args: Any, **kwargs: Any) -> Response:
        self.wiki.requests.append(request)
        status, body, headers = self.wiki.answer(request)
        response = Response()
        response.status_code = status
        response.reason = _REASONS.get(status, "")
        content_type = "text/html; charset=UTF-8" if isinstance(body, str) else "application/json; charset=utf-8"
        response.headers.update({"Content-Type": content_type, **headers})
        if isinstance(body, bytes):
            response._content = body
        else:
            response._content = (body if isinstance(body, str) else json.dumps(body)).encode()
        response._content_consumed = True
        response.encoding = "utf-8"
        response.url = request.url or ""
        response.request = request
        return response

    def close(self) -> None:
        """Nothing to release: the fake answers from memory and holds no connections."""


class FakeMediaWiki:
    """One wiki's pages and accounts. ``private`` refuses every read but tokens to an anonymous session, as a company
    wiki does; ``pluggable_auth`` renders the login form an authentication extension does, which the API cannot sign
    in through."""

    def __init__(self, page_size: int = 2, private: bool = True):
        self.page_size = page_size
        self.private = private
        self.pluggable_auth = False
        self.signed_in_as: str | None = None
        self.keeps_session = True
        self.accounts = {"Sync bot": "form-secret"}
        self.bot_passwords = {"Sync bot@pipeline": "bot-secret"}
        self.oauth_tokens = {"oauth-secret": "Sync bot"}
        self.version = "MediaWiki 1.43.11"
        self.login_redirect = "/index.php/Main_Page"
        self.category_pages: set[str] = set()
        self.pages: list[dict[str, Any]] = []
        self.files: list[dict[str, Any]] = []
        self.local_names: dict[int, str] = {}
        """Names that differ from the canonical one, as on a wiki in another language or with its own site name."""
        self.extra_namespaces: dict[int, str] = {}
        """Custom namespaces by number, with their canonical names."""
        self.downloads: list[str] = []
        self.requests: list[PreparedRequest] = []
        self.queued_failures: list[Answer] = []
        self._next_revision = 1000

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        client = Client(raise_for_status=False, request_backoff_factor=0, request_max_retry_delay=0)
        client.session.mount("https://", FakeMediaWikiTransport(self))
        client.session.mount("http://", FakeMediaWikiTransport(self))
        monkeypatch.setattr("swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client.Client", lambda **_: client)

    def add_page(
        self,
        page_id: int,
        title: str,
        *,
        namespace: int = 0,
        html: str = "<p>Body</p>",
        categories: list[str] | None = None,
        hidden_categories: list[str] | None = None,
    ) -> dict[str, Any]:
        prefix = f"{self.local_name(namespace)}:" if namespace else ""
        page = {
            "pageid": page_id,
            "ns": namespace,
            "title": f"{prefix}{title}",
            "html": html,
            "categories": list(categories or []),
            "hidden_categories": list(hidden_categories or []),
            "revisions": [],
        }
        self.pages.append(page)
        self._revise(page)
        return page

    def add_file(
        self,
        page_id: int,
        name: str,
        content: bytes,
        *,
        used_by: list[int],
        categories: list[str] | None = None,
        repository: str = "local",
        served_with: int = 200,
        pixels: tuple[int, int] = (800, 600),
    ) -> dict[str, Any]:
        """A file uploaded to the wiki and shown or linked on the given pages. ``served_with`` is the status its
        download answers with, for a file the wiki lists but will not serve; ``pixels`` its width and height."""
        file = {
            "pageid": page_id,
            "name": name,
            "content": content,
            "used_by": list(used_by),
            "categories": list(categories or []),
            "repository": repository,
            "served_with": served_with,
            "pixels": pixels,
        }
        self.files.append(file)
        return file

    def local_name(self, namespace: int) -> str:
        return self.local_names.get(namespace) or {-1: "Special", **NAMESPACES, **self.extra_namespaces}[namespace]

    def file(self, name: str) -> dict[str, Any]:
        return next(file for file in self.files if file["name"] == name)

    def page(self, page_id: int) -> dict[str, Any]:
        return next(page for page in self.pages if page["pageid"] == page_id)

    def edit(self, page_id: int, html: str) -> None:
        page = self.page(page_id)
        page["html"] = html
        self._revise(page)

    def rename(self, page_id: int, title: str) -> None:
        """A move keeps the page's id and, unlike an edit, its content."""
        page = self.page(page_id)
        prefix = f"{self.local_name(page['ns'])}:" if page["ns"] else ""
        page["title"] = f"{prefix}{title}"

    def categorize(self, page_id: int, categories: list[str]) -> None:
        """A template edit can change a page's categories without giving the page a new revision."""
        self.page(page_id)["categories"] = list(categories)

    def remove(self, page_id: int) -> None:
        self.pages = [page for page in self.pages if page["pageid"] != page_id]

    def fail_next(self, status: int, body: dict[str, Any] | str | None = None, times: int = 1) -> None:
        self.queued_failures.extend([(status, {} if body is None else body, {})] * times)

    def parses(self) -> list[int]:
        """Ids of the pages rendered, in order."""
        return [
            int(params["pageid"])
            for request in self.requests
            if (params := self._params(request)).get("action") == "parse"
        ]

    def answer(self, request: PreparedRequest) -> Answer:
        if self.queued_failures:
            return self.queued_failures.pop(0)
        path = urlparse(request.url or "").path
        params = self._params(request)
        if path == "/api.php":
            return self._api(params, request.headers.get("Authorization"))
        if path.startswith("/index.php"):
            return self._login_page(request, params)
        if path.startswith("/images/"):
            return self._download(unquote(path.removeprefix("/images/")))
        return 404, "<html>Not found</html>", {}

    def _api(self, params: dict[str, str], authorization: str | None) -> Answer:
        """An OAuth access token signs in the one request carrying it, and an unknown token fails it with a 401, as
        Wikimedia's gateway answered on 2026-10-30; otherwise the request reads as whoever the session signed in as."""
        if authorization is not None:
            reader = self.oauth_tokens.get(authorization.removeprefix("Bearer "))
            if reader is None:
                return 401, {"httpCode": 401, "httpReason": "Jwt is not in the form of Header.Payload.Signature"}, {}
            return self._signed_in_api(params, reader)
        return self._signed_in_api(params, self.signed_in_as)

    def _signed_in_api(self, params: dict[str, str], reader: str | None) -> Answer:
        if params.get("action") == "login":
            return 200, self._bot_login(params), {}
        if params.get("meta") == "tokens":
            return 200, {"query": {"tokens": {"logintoken": "token+\\"}}}, {}
        if self.private and not reader:
            return 200, {"error": {"code": "readapidenied", "info": "You need read permission to use this module."}}, {}
        if params.get("action") == "parse":
            return 200, self._parse(int(params["pageid"])), {}
        return 200, self._query(params, reader), {}

    def _query(self, params: dict[str, str], reader: str | None) -> dict[str, Any]:
        if params.get("meta") == "userinfo":
            user = {"id": 7, "name": reader} if reader else {"id": 0, "name": "127.0.0.1", "anon": True}
            return {"query": {"userinfo": user}}
        if params.get("meta") == "siteinfo":
            namespaces = {
                str(number): {"id": number, "name": self.local_name(number), **({"canonical": name} if name else {})}
                for number, name in {-1: "Special", **NAMESPACES, **self.extra_namespaces}.items()
            }
            general = {"sitename": "Acme Wiki", "generator": self.version}
            return {"query": {"general": general, "namespaces": namespaces}}
        if params.get("generator") == "allpages":
            pages = [self._listed(page) for page in self.pages if page["ns"] == int(params["gapnamespace"])]
            return self._paged(params, "gapcontinue", "pages", sorted(pages, key=lambda page: page["title"]))
        if params.get("generator") == "images":
            return self._paged(params, "gimcontinue", "pages", self._files_used_by(params["pageids"]))
        if params.get("list") == "categorymembers":
            category = params["cmtitle"].removeprefix("Category:")
            members = [
                {"pageid": entry["pageid"]} for entry in [*self.pages, *self.files] if category in entry["categories"]
            ]
            return self._paged(params, "cmcontinue", "categorymembers", members)
        if params.get("prop") == "categoryinfo":
            return {"query": {"pages": [self._category(title) for title in params["titles"].split("|")]}}
        if params.get("prop") == "revisions":
            return self._revisions(params)
        raise AssertionError(f"The fake wiki does not answer {params}")

    def _paged(self, params: dict[str, str], continue_key: str, key: str, entries: list[dict]) -> dict[str, Any]:
        start = int(params.get(continue_key, 0))
        answer: dict[str, Any] = {"batchcomplete": True}
        if entries[start : start + self.page_size]:
            answer["query"] = {key: entries[start : start + self.page_size]}
        if start + self.page_size < len(entries):
            answer["continue"] = {continue_key: str(start + self.page_size), "continue": f"{continue_key}||"}
        return answer

    def _listed(self, page: dict[str, Any]) -> dict[str, Any]:
        url = f"{SITE}/index.php/{page['title'].replace(' ', '_')}"
        return {
            "pageid": page["pageid"],
            "ns": page["ns"],
            "title": page["title"],
            "lastrevid": page["revisions"][-1][0],
            "touched": "2026-10-01T09:00:00Z",
            "fullurl": url,
            "canonicalurl": url,
        }

    def _files_used_by(self, page_ids: str) -> list[dict[str, Any]]:
        """As ``generator=images`` answers: a file of a shared repository has no page id here, and a file once per
        request however many of the pages use it."""
        wanted = {int(page_id) for page_id in page_ids.split("|")}
        return [
            {
                **({"pageid": file["pageid"]} if file["repository"] == "local" else {}),
                "ns": 6,
                "title": f"{self.local_name(6)}:{file['name']}",
                "imagerepository": file["repository"],
                "imageinfo": [
                    {
                        "size": len(file["content"]),
                        "width": file["pixels"][0],
                        "height": file["pixels"][1],
                        "sha1": hashlib.sha1(file["content"], usedforsecurity=False).hexdigest(),
                        "mime": mimetypes.guess_type(file["name"])[0] or "application/octet-stream",
                        "url": f"{SITE}/images/{quote(file['name'])}",
                        "descriptionurl": f"{SITE}/index.php/File:{quote(file['name'].replace(' ', '_'))}",
                    }
                ],
            }
            for file in self.files
            if wanted & set(file["used_by"])
        ]

    def _download(self, name: str) -> Answer:
        self.downloads.append(name)
        file = next((file for file in self.files if file["name"] == name), None)
        if file is None:
            return 404, "<html>Not found</html>", {}
        if file["served_with"] != 200:
            return file["served_with"], "<html>Refused</html>", {}
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        return 200, file["content"], {"Content-Type": mime}

    def _category(self, title: str) -> dict[str, Any]:
        name = title.removeprefix("Category:")
        size = sum(name in entry["categories"] for entry in [*self.pages, *self.files])
        entry: dict[str, Any] = {"ns": 14, "title": title}
        if name not in self.category_pages:
            entry["missing"] = True
        if size or name in self.category_pages:
            entry["categoryinfo"] = {"size": size, "pages": size, "files": 0, "subcats": 0}
        return entry

    def _revisions(self, params: dict[str, str]) -> dict[str, Any]:
        if "revids" in params:
            wanted = {int(revision) for revision in params["revids"].split("|")}
            pages = [
                {
                    "pageid": page["pageid"],
                    "revisions": [{"revid": rev, "timestamp": ts} for rev, ts in page["revisions"] if rev in wanted],
                }
                for page in self.pages
                if any(rev in wanted for rev, _ in page["revisions"])
            ]
            return {"query": {"pages": pages}}
        page = self.page(int(params["pageids"]))
        first_id, first_time = page["revisions"][0]
        return {
            "continue": {"rvcontinue": "next", "continue": "||"},
            "query": {
                "pages": [{"pageid": page["pageid"], "revisions": [{"revid": first_id, "timestamp": first_time}]}]
            },
        }

    def _parse(self, page_id: int) -> dict[str, Any]:
        page = next((page for page in self.pages if page["pageid"] == page_id), None)
        if page is None:
            return {"error": {"code": "nosuchpageid", "info": f"There is no page with ID {page_id}."}}
        categories = [{"sortkey": "", "category": name.replace(" ", "_")} for name in page["categories"]] + [
            {"sortkey": "", "category": name.replace(" ", "_"), "hidden": True} for name in page["hidden_categories"]
        ]
        return {
            "parse": {
                "title": page["title"],
                "pageid": page_id,
                "revid": page["revisions"][-1][0],
                "text": f'<div class="mw-parser-output">{page["html"]}</div>',
                "categories": categories,
            }
        }

    def _bot_login(self, params: dict[str, str]) -> dict[str, Any]:
        if self.bot_passwords.get(params.get("lgname", "")) != params.get("lgpassword"):
            return {
                "login": {"result": "Failed", "reason": "Incorrect username or password entered. Please try again."}
            }
        self._sign_in(params["lgname"].split("@")[0])
        return {"login": {"result": "Success", "lguserid": 7, "lgusername": params["lgname"].split("@")[0]}}

    def _login_page(self, request: PreparedRequest, params: dict[str, str]) -> Answer:
        path = urlparse(request.url or "").path
        if request.method == "POST":
            fields = ("username", "password") if self.pluggable_auth else ("wpName", "wpPassword")
            if self.accounts.get(params.get(fields[0], "")) != params.get(fields[1]) or "wpLoginToken" not in params:
                return 200, self._login_form(), {}
            self._sign_in(params[fields[0]])
            return 302, "", {"Location": "/index.php/Special:PluggableAuthLogin"}
        if path == "/index.php/Special:PluggableAuthLogin":
            return 302, "", {"Location": self.login_redirect}
        if params.get("title") == "Special:UserLogin":
            return 200, self._login_form(), {}
        return 200, "<html><body><h1>Main Page</h1></body></html>", {}

    def _login_form(self) -> str:
        user, password = ("username", "password") if self.pluggable_auth else ("wpName", "wpPassword")
        return (
            '<html><body><form name="userlogin" method="post" action="/index.php/Special:UserLogin">'
            f'<input name="{user}" value=""><input type="password" name="{password}">'
            '<input type="hidden" name="wpLoginToken" value="abc+\\"><input type="hidden" name="title" '
            'value="Special:UserLogin"><button name="wpLoginAttempt" value="Log in">Log in</button></form>'
            "</body></html>"
        )

    def _sign_in(self, name: str) -> None:
        if self.keeps_session:
            self.signed_in_as = name

    def _revise(self, page: dict[str, Any]) -> None:
        self._next_revision += 1
        page["revisions"].append((self._next_revision, f"2026-10-{len(page['revisions']) + 1:02d}T08:00:00Z"))

    @staticmethod
    def _params(request: PreparedRequest) -> dict[str, str]:
        query = parse_qs(urlparse(request.url or "").query)
        body = request.body.decode() if isinstance(request.body, bytes) else request.body or ""
        return {key: values[0] for key, values in {**query, **parse_qs(body)}.items()}
