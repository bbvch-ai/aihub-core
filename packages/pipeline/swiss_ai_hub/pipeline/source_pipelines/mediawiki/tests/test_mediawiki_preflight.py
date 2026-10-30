import pytest
from swiss_ai_hub.core.network import SourceHostGuard

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.tests.fake_mediawiki import SITE, FakeMediaWiki
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_options import MediaWikiOptions
from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_preflight import MediaWikiPreflight


@pytest.fixture
def wiki(monkeypatch: pytest.MonkeyPatch) -> FakeMediaWiki:
    fake = FakeMediaWiki()
    fake.add_page(1, "Welcome", categories=["Onboarding"])
    fake.add_page(2, "Lunch menu", categories=["Hide From AI"])
    fake.install(monkeypatch)
    return fake


@pytest.fixture
def guarded(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The addresses the guard was asked about; the fake site's name never reaches a real resolver."""
    checked: list[str] = []
    monkeypatch.setattr(
        SourceHostGuard, "require_public", lambda url, allowed_hosts, allow_list_variable: checked.append(url)
    )
    return checked


def _options(**changes: object) -> MediaWikiOptions:
    values = {
        "base_url": SITE,
        "auth_method": "bot_password",
        "username": "Sync bot@pipeline",
        "password": "bot-secret",
    }
    return MediaWikiOptions.model_validate({**values, **changes})


def _check(options: MediaWikiOptions) -> dict[int, str]:
    return MediaWikiPreflight.check(MediaWikiClient(options.base_url), options)


class TestPreflight:
    def test_a_good_configuration_passes_after_the_address_guard(self, wiki: FakeMediaWiki, guarded: list[str]):
        assert _check(_options(exclude_categories=["Hide From AI"])) == {0: "Main"}
        assert guarded == [SITE]

    def test_an_address_inside_the_platform_is_refused_before_any_request(self, wiki: FakeMediaWiki):
        """The sign-in sends the credentials, so nothing may be sent before the guard has passed the host."""
        with pytest.raises(ValueError, match="points at ferretdb, a name only an internal network resolves"):
            _check(_options(base_url="http://ferretdb:27017"))
        assert wiki.requests == []

    def test_a_session_that_still_reads_anonymously_is_refused(self, wiki: FakeMediaWiki, guarded: list[str]):
        """An anonymous session reads public pages only; the listing would remove everything else."""
        wiki.private = False
        wiki.keeps_session = False

        with pytest.raises(ValueError, match="still reads anonymously after signing in with Sync bot@pipeline"):
            _check(_options())

    def test_an_oauth_token_reads_as_its_account(self, wiki: FakeMediaWiki, guarded: list[str]):
        options = _options(auth_method="oauth", username="", password="", access_token="oauth-secret")

        assert MediaWikiPreflight.check(MediaWikiClient(SITE, access_token=options.oauth_token()), options) == {
            0: "Main"
        }

    def test_a_refused_oauth_token_says_what_to_check(self, wiki: FakeMediaWiki, guarded: list[str]):
        options = _options(auth_method="oauth", username="", password="", access_token="revoked")

        with pytest.raises(ValueError, match=r"refused the OAuth access token \(401\)\. Check that it is the access"):
            MediaWikiPreflight.check(MediaWikiClient(SITE, access_token=options.oauth_token()), options)

    @pytest.mark.parametrize("version", ["MediaWiki 1.27.0", "MediaWiki 1.43.11", "MediaWiki 1.48.0-wmf.1"])
    def test_every_version_since_1_27_is_accepted(self, wiki: FakeMediaWiki, guarded: list[str], version: str):
        wiki.version = version

        _check(_options())

    @pytest.mark.parametrize(
        ("version", "message"),
        [
            ("MediaWiki 1.26.4", "runs MediaWiki 1.26.4; the MediaWiki source needs 1.27 or newer"),
            ("DokuWiki 2024", "reports DokuWiki 2024, which is not a MediaWiki version"),
            ("", "reports no version"),
        ],
    )
    def test_a_wiki_too_old_or_not_mediawiki_is_refused_naming_what_it_reports(
        self, wiki: FakeMediaWiki, guarded: list[str], version: str, message: str
    ):
        wiki.version = version

        with pytest.raises(ValueError, match=message):
            _check(_options())

    def test_a_private_wiki_read_anonymously_fails_with_the_wikis_message(
        self, wiki: FakeMediaWiki, guarded: list[str]
    ):
        with pytest.raises(MediaWikiRequestError, match="readapidenied"):
            _check(_options(auth_method="anonymous"))

    @pytest.mark.parametrize(
        ("wanted", "resolved"),
        [
            (["0"], {0: "Main"}),
            (["main"], {0: "Main"}),
            (["Process", "4"], {100: "Process", 4: "Project"}),
            (["category"], {14: "Category"}),
        ],
    )
    def test_namespaces_are_resolved_by_number_or_name(
        self, wiki: FakeMediaWiki, guarded: list[str], wanted: list[str], resolved: dict[int, str]
    ):
        assert _check(_options(namespaces=wanted)) == resolved

    @pytest.mark.parametrize("wanted", ["Recipes", "-1", "Special"])
    def test_an_unknown_namespace_or_one_without_pages_is_refused(
        self, wiki: FakeMediaWiki, guarded: list[str], wanted: str
    ):
        with pytest.raises(ValueError, match=f"The wiki has no namespace {wanted}; it has 0, 1, 4, 6, 14, 100"):
            _check(_options(namespaces=[wanted]))

    def test_an_excluded_category_that_does_not_exist_fails_instead_of_excluding_nothing(
        self, wiki: FakeMediaWiki, guarded: list[str]
    ):
        """A typo would otherwise let in exactly the pages the category was meant to keep out."""
        with pytest.raises(ValueError, match="Category:Hide From A does not exist on the wiki, or Sync bot cannot"):
            _check(_options(exclude_categories=["Hide From A"]))

    def test_a_category_with_a_page_but_no_members_exists(self, wiki: FakeMediaWiki, guarded: list[str]):
        wiki.category_pages.add("Archived")

        _check(_options(include_categories=["Archived"]))
