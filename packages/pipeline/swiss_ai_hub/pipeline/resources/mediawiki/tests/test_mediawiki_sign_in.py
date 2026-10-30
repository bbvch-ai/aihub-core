import logging

import pytest

from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_client import MediaWikiClient
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_request_error import MediaWikiRequestError
from swiss_ai_hub.pipeline.resources.mediawiki.mediawiki_sign_in import MediaWikiSignIn
from swiss_ai_hub.pipeline.resources.mediawiki.tests.fake_mediawiki import SITE, FakeMediaWiki


@pytest.fixture
def wiki(monkeypatch: pytest.MonkeyPatch) -> FakeMediaWiki:
    fake = FakeMediaWiki()
    fake.add_page(1, "Welcome")
    fake.install(monkeypatch)
    return fake


def _client() -> MediaWikiClient:
    return MediaWikiClient(SITE)


class TestBotPassword:
    def test_a_bot_password_signs_the_session_in(self, wiki: FakeMediaWiki):
        client = _client()

        MediaWikiSignIn.sign_in(client, "bot_password", "Sync bot@pipeline", "bot-secret")

        assert client.user_info()["name"] == "Sync bot"

    def test_a_refused_bot_password_names_the_account_and_the_alternative(self, wiki: FakeMediaWiki):
        with pytest.raises(ValueError, match="refused the bot password of Sync bot@pipeline: Incorrect.*web form"):
            MediaWikiSignIn.sign_in(_client(), "bot_password", "Sync bot@pipeline", "wrong")

    def test_the_password_is_never_logged(self, wiki: FakeMediaWiki, caplog: pytest.LogCaptureFixture):
        """dlt's REST client logs form data at debug level; the credentials go through the bare session."""
        caplog.set_level(logging.DEBUG)

        MediaWikiSignIn.sign_in(_client(), "bot_password", "Sync bot@pipeline", "bot-secret")

        assert "bot-secret" not in caplog.text


class TestWebForm:
    @pytest.mark.parametrize("pluggable_auth", [False, True])
    def test_the_login_page_signs_the_session_in_whatever_its_field_names(
        self, wiki: FakeMediaWiki, pluggable_auth: bool
    ):
        wiki.pluggable_auth = pluggable_auth
        client = _client()

        MediaWikiSignIn.sign_in(client, "web_form", "Sync bot", "form-secret")

        assert client.user_info()["name"] == "Sync bot"

    def test_the_form_is_posted_with_its_hidden_fields(self, wiki: FakeMediaWiki):
        MediaWikiSignIn.sign_in(_client(), "web_form", "Sync bot", "form-secret")

        posted = next(request for request in wiki.requests if request.method == "POST")
        assert FakeMediaWiki._params(posted)["wpLoginToken"] == "abc+\\"

    def test_a_page_that_still_shows_the_form_refused_the_credentials(self, wiki: FakeMediaWiki):
        with pytest.raises(ValueError, match="refused the user name or password of Sync bot"):
            MediaWikiSignIn.sign_in(_client(), "web_form", "Sync bot", "wrong")

    def test_a_redirect_to_another_host_is_not_followed(self, wiki: FakeMediaWiki):
        """The session's cookies, and the address guard's check, are for the wiki's host alone."""
        wiki.login_redirect = "https://elsewhere.test/collect"

        with pytest.raises(ValueError, match="redirected to https://elsewhere.test/collect"):
            MediaWikiSignIn.sign_in(_client(), "web_form", "Sync bot", "form-secret")
        assert all("elsewhere" not in (request.url or "") for request in wiki.requests)

    def test_a_downgrade_to_http_is_not_followed(self, wiki: FakeMediaWiki):
        wiki.login_redirect = "http://wiki.acme.test/index.php/Main_Page"

        with pytest.raises(ValueError, match="only the wiki's host is followed"):
            MediaWikiSignIn.sign_in(_client(), "web_form", "Sync bot", "form-secret")

    def test_a_page_without_a_login_form_is_named(self, wiki: FakeMediaWiki):
        wiki.fail_next(200, "<html><body>Maintenance</body></html>")

        with pytest.raises(ValueError, match="shows no login form"):
            MediaWikiSignIn.sign_in(_client(), "web_form", "Sync bot", "form-secret")


class TestOAuth:
    def test_the_access_token_reads_as_its_account_on_every_request(self, wiki: FakeMediaWiki):
        client = MediaWikiClient(SITE, access_token="oauth-secret")

        MediaWikiSignIn.sign_in(client, "oauth", "", "")

        assert client.user_info()["name"] == "Sync bot"
        assert wiki.requests[0].headers["Authorization"] == "Bearer oauth-secret"

    def test_an_unknown_token_fails_with_the_gateways_reason(self, wiki: FakeMediaWiki):
        with pytest.raises(MediaWikiRequestError, match="401 Unauthorized to GET /api.php: Jwt is not in the form"):
            MediaWikiClient(SITE, access_token="expired").user_info()

    def test_the_token_is_never_logged(self, wiki: FakeMediaWiki, caplog: pytest.LogCaptureFixture):
        """dlt's REST client logs a request's headers at debug level; the token goes in through ``auth``."""
        caplog.set_level(logging.DEBUG)

        MediaWikiClient(SITE, access_token="oauth-secret").user_info()

        assert "oauth-secret" not in caplog.text


@pytest.mark.parametrize("method", ["anonymous", "oauth"])
def test_methods_without_a_sign_in_send_nothing(wiki: FakeMediaWiki, method: str):
    MediaWikiSignIn.sign_in(_client(), method, "", "")

    assert wiki.requests == []
