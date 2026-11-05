import pytest

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.tests.fake_mediawiki import SHARED, SITE, FakeMediaWiki


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

        client = MediaWikiClient(SITE)
        with pytest.raises(ValueError, match="repeated its continuation"):
            _listed_ids(client)

    def test_category_members_are_collected_across_pages(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        for page_id in (1, 3, 5):
            wiki.categorize(page_id, ["Hide From AI"])

        assert MediaWikiClient(SITE).category_member_ids("Hide From AI") == {1, 3, 5}

    def test_subcategories_are_followed_only_when_asked_and_once_each(self, monkeypatch: pytest.MonkeyPatch):
        """Category trees can loop: here Archive sits in Projects, and Projects in Archive."""
        wiki = _wiki(monkeypatch)
        wiki.add_page(20, "Projects", namespace=14, categories=["Archive"])
        wiki.add_page(21, "Archive", namespace=14, categories=["Projects"])
        wiki.categorize(1, ["Projects"])
        wiki.categorize(2, ["Archive"])

        assert MediaWikiClient(SITE).category_member_ids("Projects") == {1, 21}
        assert MediaWikiClient(SITE).category_member_ids("Projects", with_subcategories=True) == {1, 2, 20, 21}

    def test_a_user_agent_goes_with_every_request(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)

        _listed_ids(MediaWikiClient(SITE, user_agent="AcmeKnowledgeSync/1.0 (it@acme.ch)"))

        assert {request.headers["User-Agent"] for request in wiki.requests} == {"AcmeKnowledgeSync/1.0 (it@acme.ch)"}


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

        client = MediaWikiClient(SITE)
        with pytest.raises(
            MediaWikiRequestError, match=r"refused GET /api.php \(readapidenied\): You need read"
        ) as error:
            client.site_info()
        assert error.value.code == "readapidenied"

    def test_an_error_status_carries_mediawikis_own_error(self, monkeypatch: pytest.MonkeyPatch):
        """A wiki without a gateway in front answers a refused request with its own error object."""
        wiki = _wiki(monkeypatch)
        wiki.fail_next(403, {"error": {"code": "mwoauth-invalid-authorization", "info": "Invalid access token"}})

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError, match="403 Forbidden to GET /api.php: Invalid access token") as error:
            client.site_info()
        assert error.value.code == "mwoauth-invalid-authorization"

    def test_a_rate_limited_request_is_retried(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        wiki.fail_next(429)

        assert _listed_ids(MediaWikiClient(SITE)) == [1, 2, 3, 4, 5]

    def test_a_redirect_is_not_followed(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch)
        wiki.queued_failures.append((302, "", {"Location": "https://elsewhere.test/api.php"}))

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError, match="redirects to https://elsewhere.test/api.php"):
            client.site_info()
        assert len(wiki.requests) == 1

    def test_an_html_answer_points_at_the_wiki_url(self, monkeypatch: pytest.MonkeyPatch):
        """A single sign-on gateway answers an expired session with its login page, not with JSON."""
        wiki = _wiki(monkeypatch)
        wiki.fail_next(200, "<html>Sign in</html>")

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError, match="instead of JSON; the wiki URL must be the folder"):
            client.site_info()


class TestFiles:
    def test_each_file_the_pages_use_is_listed_once_with_its_checksum_and_urls(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=3)
        wiki.add_file(101, "Handbook 2026.pdf", b"%PDF-1.7 handbook", used_by=[1, 2])
        wiki.add_file(102, "Logo.png", b"PNG", used_by=[3], repository="shared")
        wiki.add_file(103, "Unused.pdf", b"%PDF-1.7 unused", used_by=[])

        files = {file["title"]: file for file in MediaWikiClient(SITE).files_used_by([1, 2, 3])}

        assert sorted(files) == ["File:Handbook 2026.pdf", "File:Logo.png"]
        handbook = files["File:Handbook 2026.pdf"]
        assert handbook["pageid"] == 101
        assert handbook["imagerepository"] == "local"
        assert handbook["imageinfo"]["size"] == len(b"%PDF-1.7 handbook")
        assert handbook["imageinfo"]["url"] == f"{SITE}/images/Handbook%202026.pdf"
        assert files["File:Logo.png"]["imagerepository"] == "shared"

    def test_a_file_is_downloaded_with_the_session(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)
        wiki.add_file(101, "Handbook.pdf", b"%PDF-1.7 handbook", used_by=[1])

        assert MediaWikiClient(SITE).download(f"{SITE}/images/Handbook.pdf", max_bytes=1_000) == b"%PDF-1.7 handbook"

    def test_an_oauth_token_goes_with_a_download_from_the_wiki_but_not_to_another_host(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """A private wiki serves its files to a signed-in reader only; a separate upload host is another party."""
        wiki = _wiki(monkeypatch, pages=1)
        wiki.private = True
        wiki.add_file(101, "Handbook.pdf", b"%PDF-1.7 handbook", used_by=[1])
        client = MediaWikiClient(SITE, access_token="oauth-secret")

        assert client.download(f"{SITE}/images/Handbook.pdf", max_bytes=1_000) == b"%PDF-1.7 handbook"
        with pytest.raises(MediaWikiRequestError):
            client.download("https://upload.acme.test/images/Handbook.pdf", max_bytes=1_000)
        assert wiki.requests[-1].headers.get("Authorization") is None

    def test_a_file_of_the_wiki_is_reached_at_the_configured_address(self, monkeypatch: pytest.MonkeyPatch):
        """MediaWiki builds file URLs from its own server setting: another name, or http behind a TLS proxy. The
        session and the token belong to the address the pipeline uses."""
        wiki = _wiki(monkeypatch, pages=1)
        wiki.server = "http://wiki.public.test"
        wiki.add_file(101, "Handbook.pdf", b"%PDF-1.7 handbook", used_by=[1])
        wiki.add_file(102, "Logo.png", b"PNG", used_by=[1], repository="shared")

        urls = {file["title"]: file["imageinfo"]["url"] for file in MediaWikiClient(SITE).files_used_by([1])}

        assert urls["File:Handbook.pdf"] == f"{SITE}/images/Handbook.pdf"
        assert urls["File:Logo.png"] == f"{SHARED}/images/Logo.png"

    def test_a_file_larger_than_the_limit_is_not_held(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)
        wiki.add_file(101, "Handbook.pdf", b"%PDF-1.7 handbook", used_by=[1])

        assert MediaWikiClient(SITE).download(f"{SITE}/images/Handbook.pdf", max_bytes=5) is None

    def test_a_refused_download_names_its_status(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)
        wiki.add_file(101, "Secret.pdf", b"%PDF-1.7 secret", used_by=[1], served_with=403)

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError) as refused:
            client.download(f"{SITE}/images/Secret.pdf", max_bytes=1_000)
        assert refused.value.status_code == 403

    def test_an_html_page_instead_of_the_file_is_refused(self, monkeypatch: pytest.MonkeyPatch):
        """A single sign-on gateway answers an expired session with its login page and status 200."""
        wiki = _wiki(monkeypatch, pages=1)
        wiki.fail_next(200, "<html>Sign in</html>")

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError, match="HTML page instead of the file"):
            client.download(f"{SITE}/images/Handbook.pdf", max_bytes=1_000)

    def test_a_download_does_not_follow_a_redirect(self, monkeypatch: pytest.MonkeyPatch):
        wiki = _wiki(monkeypatch, pages=1)
        wiki.queued_failures.append((302, "", {"Location": "https://elsewhere.test/Handbook.pdf"}))

        client = MediaWikiClient(SITE)
        with pytest.raises(MediaWikiRequestError, match="redirects to https://elsewhere.test/Handbook.pdf"):
            client.download(f"{SITE}/images/Handbook.pdf", max_bytes=1_000)
