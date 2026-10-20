import pytest
from pydantic import ValidationError

from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_options import ConfluenceOptions


def _options(**changes: object) -> ConfluenceOptions:
    values = {
        "base_url": "https://acme.atlassian.net/wiki",
        "deployment": "cloud",
        "email": "bot@acme.test",
        "api_token": "s3cret-token",
        "space_keys": ["ENG"],
        **changes,
    }
    return ConfluenceOptions.model_validate(values)


class TestProblems:
    def test_a_complete_configuration_has_none(self):
        assert _options().problems() == []

    def test_data_center_needs_no_e_mail(self):
        assert _options(deployment="data_center", email="").problems() == []

    @pytest.mark.parametrize(
        ("change", "problem"),
        [
            ({"base_url": ""}, "the Confluence URL is missing"),
            ({"api_token": ""}, "the token is missing"),
            ({"email": ""}, "Confluence Cloud needs the e-mail of the account the API token belongs to"),
            ({"space_keys": None}, "no space key is given"),
            ({"space_keys": [" "]}, "no space key is given"),
            ({"ancestor_page_ids": ["123", "12a"]}, "12a is not a Confluence page ID"),
        ],
    )
    def test_each_problem_is_worded_for_whoever_entered_it(self, change: dict[str, object], problem: str):
        assert _options(**change).problems() == [problem]

    def test_a_page_id_in_another_script_is_not_a_digit_here(self):
        assert _options(ancestor_page_ids=["١٢٣"]).problems() == ["١٢٣ is not a Confluence page ID"]

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://acme.test",
            "https://bot:token@acme.atlassian.net/wiki",
            "acme.atlassian.net",
            "https://a b",
            "http://seaweedfs-filer:8888/buckets/other/x.md?",
            "https://confluence.acme.ch#",
            "https://acme.atlassian.net/wiki?os_authType=basic",
        ],
    )
    def test_a_url_that_is_not_plain_http_is_refused_when_saved(self, url: str):
        """A query or fragment would turn the API path appended to the URL into a query, so it could name any path."""
        with pytest.raises(ValidationError):
            _options(base_url=url)


class TestScope:
    def test_only_the_configured_spaces_are_searched(self):
        assert _options(space_keys=["OPS", "ENG"]).scope_cql() == 'type = page and space in ("ENG", "OPS")'

    def test_labels_and_parent_pages_narrow_the_scope(self):
        cql = _options(labels=["runbook"], ancestor_page_ids=["456", "123"]).scope_cql()

        assert cql == (
            'type = page and space in ("ENG") and label in ("runbook") and (ancestor in (123, 456) or id in (123, 456))'
        )

    def test_quotes_and_backslashes_cannot_end_a_value(self):
        """Whoever configures the database writes these values; they must stay inside their quotes."""
        cql = _options(space_keys=['ENG") or space != ("X'], labels=["a\\"]).scope_cql()

        assert 'space in ("ENG\\") or space != (\\"X")' in cql
        assert 'label in ("a\\\\")' in cql

    def test_the_same_scope_typed_in_another_order_is_stored_the_same(self):
        """The scope fingerprint is taken from the stored values; a reordering must not re-read every page."""
        first = _options(space_keys=["OPS", "ENG"], labels=["b", "a", "a"])
        second = _options(space_keys=[" ENG", "OPS "], labels=["a", "b"])

        assert (first.space_keys, first.labels) == (second.space_keys, second.labels) == (["ENG", "OPS"], ["a", "b"])

    def test_a_personal_space_keeps_its_case(self):
        assert _options(space_keys=["~5d1a2b3c4e"]).spaces() == ["~5d1a2b3c4e"]

    def test_an_untouched_group_validates_as_blank_settings(self):
        """While another kind is selected, this group submits nothing and must still validate."""
        blank = ConfluenceOptions.model_validate({"space_keys": "", "labels": "", "ancestor_page_ids": ""})

        assert (blank.spaces(), blank.page_labels(), blank.parent_pages()) == ([], [], [])
