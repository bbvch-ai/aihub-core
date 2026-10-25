import pytest
from swiss_ai_hub.core.network import PublicHostGuard

from swiss_ai_hub.pipeline.resources.confluence.confluence_client import ConfluenceClient
from swiss_ai_hub.pipeline.resources.confluence.confluence_request_error import ConfluenceRequestError
from swiss_ai_hub.pipeline.resources.confluence.tests.fake_confluence import FakeConfluence
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_options import ConfluenceOptions
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_preflight import ConfluencePreflight


@pytest.fixture(params=["cloud", "data_center"])
def confluence(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> FakeConfluence:
    fake = FakeConfluence(deployment=request.param)
    fake.add_page("100", "Runbooks", space="ENG")
    fake.add_page("200", "Incidents", space="OPS")
    fake.install(monkeypatch)
    return fake


@pytest.fixture
def guarded(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """The addresses the guard was asked about; the fake site's name never reaches a real resolver."""
    checked: list[str] = []
    monkeypatch.setattr(
        PublicHostGuard, "require_public", lambda url, allowed_hosts, allow_list_setting: checked.append(url)
    )
    return checked


def _options(confluence: FakeConfluence, **changes: object) -> ConfluenceOptions:
    values = {
        "base_url": confluence.site,
        "deployment": confluence.deployment,
        "email": "bot@acme.test" if confluence.deployment == "cloud" else "",
        "api_token": "s3cret-token",
        "space_keys": ["ENG", "OPS"],
        **changes,
    }
    return ConfluenceOptions.model_validate(values)


def _check(options: ConfluenceOptions) -> None:
    client = ConfluenceClient(options.base_url, options.deployment, options.email, options.api_token)
    ConfluencePreflight.check(client, options)


class TestPreflight:
    def test_a_good_configuration_passes_after_the_address_guard(self, confluence: FakeConfluence, guarded: list[str]):
        _check(_options(confluence, ancestor_page_ids=["100"]))

        assert guarded == [confluence.site]

    def test_an_address_inside_the_platform_is_refused_before_any_request(self, confluence: FakeConfluence):
        options = _options(confluence, base_url="http://ferretdb:27017")

        with pytest.raises(ValueError, match="points at ferretdb, a name only an internal network resolves"):
            _check(options)
        assert confluence.requests == []

    @pytest.mark.parametrize("status", [401, 403])
    def test_rejected_credentials_name_the_site_and_what_to_check(
        self, confluence: FakeConfluence, guarded: list[str], status: int
    ):
        confluence.fail_next(status)
        options = _options(confluence)

        with pytest.raises(ValueError, match=rf"rejected the credentials for {confluence.site} \({status}\)\. Check"):
            _check(options)

    def test_an_anonymous_answer_is_refused(self, confluence: FakeConfluence, guarded: list[str]):
        """Anonymous access reads public pages only; the listing would remove everything else."""
        confluence.account = {"type": "anonymous"}
        options = _options(confluence)

        with pytest.raises(ValueError, match="as if no credentials were sent"):
            _check(options)

    def test_a_space_the_account_cannot_see_is_named_with_the_account(
        self, confluence: FakeConfluence, guarded: list[str]
    ):
        options = _options(confluence, space_keys=["ENG", "SALES"])

        with pytest.raises(ValueError, match="Confluence space SALES does not exist, or Sync Bot cannot see it"):
            _check(options)

    def test_a_missing_parent_page_is_named(self, confluence: FakeConfluence, guarded: list[str]):
        options = _options(confluence, ancestor_page_ids=["999"])

        with pytest.raises(ValueError, match="Confluence page 999 does not exist, or Sync Bot cannot see it"):
            _check(options)

    def test_a_parent_page_outside_the_spaces_is_refused(self, confluence: FakeConfluence, guarded: list[str]):
        options = _options(confluence, space_keys=["ENG"], ancestor_page_ids=["200"])

        with pytest.raises(ValueError, match="page 200 is in space OPS, which is not one of the database's spaces"):
            _check(options)

    def test_a_failing_site_is_not_mistaken_for_wrong_credentials(self, confluence: FakeConfluence, guarded: list[str]):
        confluence.fail_next(500, times=10)
        options = _options(confluence)

        with pytest.raises(ConfluenceRequestError, match="500"):
            _check(options)
