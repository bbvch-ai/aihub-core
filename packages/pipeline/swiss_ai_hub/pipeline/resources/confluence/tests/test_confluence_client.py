import base64
from urllib.parse import parse_qs, urlparse

import pytest

from swiss_ai_hub.pipeline.resources.confluence.confluence_client import ConfluenceClient
from swiss_ai_hub.pipeline.resources.confluence.confluence_request_error import ConfluenceRequestError
from swiss_ai_hub.pipeline.resources.confluence.tests.fake_confluence import SITES, FakeConfluence

_TOKEN = "s3cret-token"


def _confluence(monkeypatch: pytest.MonkeyPatch, deployment: str = "cloud", pages: int = 5) -> FakeConfluence:
    confluence = FakeConfluence(deployment=deployment)
    for number in range(1, pages + 1):
        confluence.add_page(str(number), f"Page {number}")
    confluence.install(monkeypatch)
    return confluence


def _client(deployment: str = "cloud") -> ConfluenceClient:
    return ConfluenceClient(
        base_url=f"{SITES[deployment]}/", deployment=deployment, email="bot@acme.test", token=_TOKEN
    )


def _ids(client: ConfluenceClient) -> list[str]:
    return [page["id"] for results in client.search('type = page and space in ("ENG")', "version") for page in results]


class TestSearch:
    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    def test_every_page_is_returned_following_next_links_below_the_site(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        """Cloud's site is …/wiki and Data Center's has no path; a link joined onto the host would lose /wiki."""
        confluence = _confluence(monkeypatch, deployment)

        assert _ids(_client(deployment)) == ["1", "2", "3", "4", "5"]
        assert len(confluence.searches()) == 3

    def test_the_query_and_expansions_are_sent_as_given(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)

        _ids(_client())

        assert confluence.searches()[0] == {
            "cql": 'type = page and space in ("ENG")',
            "expand": "version",
            "limit": str(ConfluenceClient.PAGE_SIZE),
        }

    def test_pages_are_read_by_id_in_batches(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch, pages=30)
        confluence.page_size = 50

        pages = [
            page
            for results in _client().pages_by_id([str(n) for n in range(1, 31)], "body.storage")
            for page in results
        ]

        assert len(pages) == 30
        assert pages[0]["body"]["storage"]["value"] == "<p>Body</p>"
        assert [search["cql"] for search in confluence.searches()] == [
            f"id in ({', '.join(str(n) for n in range(1, 26))})",
            "id in (26, 27, 28, 29, 30)",
        ]

    def test_a_next_link_leaving_the_site_is_refused(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)
        confluence.next_link_prefix = "@elsewhere.test"
        client = _client()

        with pytest.raises(ValueError, match="next page outside the site"):
            _ids(client)


class TestAuthentication:
    def test_cloud_signs_in_with_the_e_mail_and_api_token(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)

        _client().current_user()

        expected = base64.b64encode(f"bot@acme.test:{_TOKEN}".encode()).decode()
        assert confluence.requests[0].headers["Authorization"] == f"Basic {expected}"

    def test_data_center_signs_in_with_the_personal_access_token(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch, "data_center")

        _client("data_center").current_user()

        assert confluence.requests[0].headers["Authorization"] == f"Bearer {_TOKEN}"


class TestErrors:
    def test_a_refused_sign_in_fails_at_once_naming_status_and_path(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)
        confluence.fail_next(401, {"message": "Basic authentication with passwords is deprecated."}, times=3)
        client = _client()

        with pytest.raises(ConfluenceRequestError) as refused:
            client.current_user()

        assert refused.value.status_code == 401
        assert str(refused.value) == (
            "Confluence answered 401 Unauthorized to GET /wiki/rest/api/user/current: "
            "Basic authentication with passwords is deprecated."
        )
        assert _TOKEN not in str(refused.value)
        assert len(confluence.requests) == 1

    @pytest.mark.parametrize("status", [429, 503])
    def test_a_busy_or_unavailable_site_is_retried(self, monkeypatch: pytest.MonkeyPatch, status: int):
        confluence = _confluence(monkeypatch)
        confluence.fail_next(status, headers={"Retry-After": "0"})

        assert _ids(_client()) == ["1", "2", "3", "4", "5"]
        assert len(confluence.searches()) == 4

    def test_an_error_without_a_json_body_stays_retryable(self, monkeypatch: pytest.MonkeyPatch):
        """A gateway in front of Confluence answers 502 with an empty body; it must not turn into a parsing error."""
        confluence = _confluence(monkeypatch)
        confluence.fail_next(502, b"")

        assert _ids(_client()) == ["1", "2", "3", "4", "5"]

    def test_a_redirect_is_refused_and_not_followed(self, monkeypatch: pytest.MonkeyPatch):
        """The address guard checked the configured host only; a redirect could lead anywhere."""
        confluence = _confluence(monkeypatch)
        confluence.fail_next(302, headers={"Location": "http://ferretdb:27017/"})
        client = _client()

        with pytest.raises(ConfluenceRequestError, match="it redirects to http://ferretdb:27017/"):
            client.current_user()
        assert len(confluence.requests) == 1

    def test_a_missing_endpoint_carries_confluence_s_own_message(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)
        confluence.fail_next(404, {"message": "No space with key : OPS"})
        client = _client()

        with pytest.raises(ConfluenceRequestError, match="404 Not Found to GET /wiki/rest/api/search: No space"):
            client.find_space("OPS")


class TestLookups:
    """Cloud's REST v1 no longer serves a space by key or a page by ID, so both are found through CQL search."""

    @pytest.mark.parametrize("deployment", ["cloud", "data_center"])
    def test_a_space_the_account_can_see_is_found_and_any_other_is_not(
        self, monkeypatch: pytest.MonkeyPatch, deployment: str
    ):
        confluence = _confluence(monkeypatch, deployment)

        assert _client(deployment).find_space("ENG") == {
            "entityType": "space",
            "space": {"key": "ENG", "name": "ENG space"},
        }
        assert _client(deployment).find_space("OPS") is None
        assert all("/rest/api/space/" not in request.url for request in confluence.requests)

    def test_a_space_key_cannot_break_out_of_its_quotes(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)

        assert _client().find_space('ENG" or type = page or space = "X') is None

        [cql] = parse_qs(urlparse(confluence.requests[-1].url).query)["cql"]
        assert cql == 'type = space and space = "ENG\\" or type = page or space = \\"X"'

    def test_a_page_is_found_with_its_space_and_without_its_body(self, monkeypatch: pytest.MonkeyPatch):
        confluence = _confluence(monkeypatch)
        confluence.add_page("42", "Runbook", space="OPS")

        page = _client().find_page("42")

        assert (page["id"], page["space"]["key"], "body" in page) == ("42", "OPS", False)
        assert _client().find_page("999") is None
