import pytest

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.tests.fake_mediawiki import SITE, FakeMediaWiki


def _wiki(monkeypatch: pytest.MonkeyPatch, pages: int = 5) -> FakeMediaWiki:
    wiki = FakeMediaWiki(private=False)
    for number in range(1, pages + 1):
        wiki.add_page(number, f"Page {number}")
    wiki.install(monkeypatch)
    return wiki


def _listed_ids(client: MediaWikiClient, namespace: int = 0) -> list[int]:
    return [page["pageid"] for batch in client.pages(namespace) for page in batch]


class TestListing:
    def test_every_page_is_returned_following_the_continuation(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)

        assert _listed_ids(MediaWikiClient(f"{SITE}/")) == [1, 2, 3, 4, 5]
        assert len(wiki.requests) == 3

    def test_the_listing_leaves_out_redirects_and_asks_for_revisions_and_urls(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)

        _listed_ids(MediaWikiClient(SITE), namespace=100)

        params = FakeMediaWiki._params(wiki.requests[0])
        assert params["gapnamespace"] == "100"
        assert params["gapfilterredir"] == "nonredirects"
        assert params["prop"] == "info"
        assert params["inprop"] == "url"

    def test_a_namespace_without_pages_lists_nothing(self, monkeypatch: pytest.MonkeyPatch):
        _wiki(monkeypatch)

        assert _listed_ids(MediaWikiClient(SITE), namespace=4) == []

    def test_a_repeated_continuation_fails_instead_of_looping(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        stuck = {"continue": {"gapcontinue": "2", "continue": "gapcontinue||"}, "query": {"pages": []}}
        wiki.fail_next(200, stuck, times=2)

        with pytest.raises(ValueError, match="repeated its continuation"):
            _listed_ids(MediaWikiClient(SITE))

    def test_category_members_are_collected_across_pages(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        for page_id in (1, 3, 5):
            wiki.categorize(page_id, ["Hide From AI"])

        assert MediaWikiClient(SITE).category_member_ids("Hide From AI") == {1, 3, 5}


class TestRevisions:
    def test_the_creation_time_is_read_from_the_oldest_revision_without_paging_on(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        wiki = _wiki(monkeypatch, pages=1)
        wiki.edit(1, "<p>Edited</p>")

        assert MediaWikiClient(SITE).first_revision_time(1) == "2026-10-01T08:00:00Z"
        assert len(wiki.requests) == 1

    def test_revision_times_are_read_in_batches(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=60)
        revisions = [page["revisions"][-1][0] for page in wiki.pages]

        times = MediaWikiClient(SITE).revision_times(revisions)

        assert set(times) == set(revisions)
        assert len(wiki.requests) == 2


class TestParse:
    def test_a_page_is_rendered_without_edit_links_toc_or_limit_report(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)

        parsed = MediaWikiClient(SITE).parse(1)

        assert parsed is not None and parsed["revid"] == wiki.page(1)["revisions"][-1][0]
        params = FakeMediaWiki._params(wiki.requests[0])
        assert {params["disableeditsection"], params["disabletoc"], params["disablelimitreport"]} == {"1"}

    def test_a_page_deleted_since_the_listing_is_none(self, monkeypatch: pytest.MonkeyPatch):
        _wiki(monkeypatch, pages=1)

        assert MediaWikiClient(SITE).parse(99) is None


class TestErrors:
    def test_an_api_error_names_its_code_and_message(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        wiki.private = True

        with pytest.raises(
            MediaWikiRequestError, match=r"refused GET /api.php \(readapidenied\): You need read"
        ) as error:
            MediaWikiClient(SITE).site_info()
        assert error.value.code == "readapidenied"

    def test_an_error_status_carries_mediawikis_own_error(self, monkeypatch: pytest.MonkeyPatch):
        """A wiki without a gateway in front answers a refused request with its own error object."""
        wiki = _wiki(monkeypatch)
        wiki.fail_next(403, {"error": {"code": "mwoauth-invalid-authorization", "info": "Invalid access token"}})

        with pytest.raises(MediaWikiRequestError, match="403 Forbidden to GET /api.php: Invalid access token") as error:
            MediaWikiClient(SITE).site_info()
        assert error.value.code == "mwoauth-invalid-authorization"

    def test_a_rate_limited_request_is_retried(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        wiki.fail_next(429)

        assert _listed_ids(MediaWikiClient(SITE)) == [1, 2, 3, 4, 5]

    def test_a_redirect_is_not_followed(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        wiki.queued_failures.append((302, "", {"Location": "https://elsewhere.test/api.php"}))

        with pytest.raises(MediaWikiRequestError, match="redirects to https://elsewhere.test/api.php"):
            MediaWikiClient(SITE).site_info()
        assert len(wiki.requests) == 1

    def test_an_html_answer_points_at_the_wiki_url(self, monkeypatch: pytest.MonkeyPatch):
        """A single sign-on gateway answers an expired session with its login page, not with JSON."""
        wiki = _wiki(monkeypatch)
        wiki.fail_next(200, "<html>Sign in</html>")

        with pytest.raises(MediaWikiRequestError, match="instead of JSON; the wiki URL must be the folder"):
            MediaWikiClient(SITE).site_info()
