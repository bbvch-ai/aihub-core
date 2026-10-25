import logging

import pytest
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.network import PublicHostGuard

from swiss_ai_hub.pipeline.resources.confluence.tests.fake_confluence import SITES, FakeConfluence
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_adapter import ConfluenceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig


@pytest.fixture(autouse=True)
def no_active_dlt_pipeline() -> None:
    """Outside a pipeline, dlt resolves state from whichever pipeline last ran in this process."""
    Container()[PipelineContext].deactivate()


@pytest.fixture(autouse=True)
def external_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fake site's name must never reach a real resolver; the guard has tests of its own."""
    monkeypatch.setattr(PublicHostGuard, "require_public", lambda url, allowed_hosts, allow_list_setting: None)


@pytest.fixture
def confluence(monkeypatch: pytest.MonkeyPatch) -> FakeConfluence:
    fake = FakeConfluence(page_size=2)
    fake.add_page("1", "Engineering")
    fake.add_page("2", "Runbooks", ancestors=[("1", "Engineering")])
    fake.add_page("3", "Deploy", ancestors=[("1", "Engineering"), ("2", "Runbooks")], labels=["runbook"])
    fake.add_page("10", "Operations", space="OPS")
    fake.install(monkeypatch)
    return fake


def _config(**confluence: object) -> StructuredSyncConfig:
    options = {
        "base_url": SITES["cloud"],
        "deployment": "cloud",
        "email": "bot@acme.test",
        "api_token": "s3cret-token",
        "space_keys": ["ENG", "OPS"],
        **confluence,
    }
    return StructuredSyncConfig.model_validate({"source_kind": "confluence", "confluence": options})


def _files(config: StructuredSyncConfig) -> dict[str, str]:
    rows = config.adapter().file_source(config.options())
    return {
        row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]: row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN]
        for row in rows
    }


class TestSync:
    def test_every_page_becomes_a_file_in_its_space_with_its_tree_as_folders(self, confluence: FakeConfluence):
        files = _files(_config())

        assert set(files) == {
            "ENG/Engineering.md",
            "ENG/Engineering/Runbooks.md",
            "ENG/Engineering/Runbooks/Deploy.md",
            "OPS/Operations.md",
        }
        assert "labels:\n- runbook\n" in files["ENG/Engineering/Runbooks/Deploy.md"]
        assert "\n# Deploy\n" in files["ENG/Engineering/Runbooks/Deploy.md"]

    def test_the_listing_names_exactly_the_files_the_sync_writes(self, confluence: FakeConfluence):
        """A listed key without its file, or a file never listed, would make the reconcile step delete data."""
        config = _config()

        assert config.adapter().list_record_paths(config.options()) == set(_files(config))

    def test_an_archived_page_is_neither_written_nor_listed(self, confluence: FakeConfluence):
        confluence.add_page("4", "Old plan", ancestors=[("1", "Engineering")], status="archived")
        config = _config()

        assert "ENG/Engineering/Old plan.md" not in _files(config)
        assert "ENG/Engineering/Old plan.md" not in config.adapter().list_record_paths(config.options())

    def test_two_pages_sharing_a_file_are_named_in_the_log(
        self, confluence: FakeConfluence, caplog: pytest.LogCaptureFixture
    ):
        confluence.add_page("5", "Q1/Q2", ancestors=[("1", "Engineering")])
        confluence.add_page("6", "Q1_Q2", ancestors=[("1", "Engineering")])
        config = _config()

        with caplog.at_level(logging.WARNING):
            paths = config.adapter().list_record_paths(config.options())

        assert "ENG/Engineering/Q1_Q2.md" in paths
        assert "Confluence pages 5 and 6 share the file ENG/Engineering/Q1_Q2.md" in caplog.text


class TestUnusableConfiguration:
    @pytest.mark.parametrize(
        ("options", "reason"),
        [
            ({"space_keys": None}, "no space key is given"),
            ({"ancestor_page_ids": ["12a"]}, "12a is not a Confluence page ID"),
            ({"email": ""}, "Confluence Cloud needs the e-mail"),
            ({"api_token": ""}, "the token is missing"),
            ({"base_url": ""}, "the Confluence URL is missing"),
        ],
    )
    def test_the_sync_fails_naming_what_to_fix_before_any_request(
        self, confluence: FakeConfluence, options: dict, reason: str
    ):
        config = _config(**options)
        adapter, source_options = config.adapter(), config.options()

        with pytest.raises(ValueError, match=reason):
            adapter.dlt_source(source_options)
        with pytest.raises(ValueError, match=reason):
            adapter.list_record_paths(source_options)
        assert confluence.requests == []


class TestForm:
    def test_the_token_is_the_one_secret(self):
        secrets = {path for path in StructuredSyncConfig.secret_field_paths() if path.startswith("confluence.")}

        assert secrets == {"confluence.api_token"}

    def test_the_email_is_asked_only_for_confluence_cloud(self):
        [group] = [
            element for element in StructuredSyncConfig.as_form().to_formkit_form() if element.name == "confluence"
        ]
        email = next(child for child in group.children if child.name == "email")

        assert email.condition_if == (
            "$get(structured_source_kind).value === 'confluence' && $get(confluence_deployment).value === 'cloud'"
        )

    def test_the_group_shows_whatever_the_edition(self):
        """Its conditions are combined with || and FormKit gives && no precedence: unparenthesised, the group would
        hide until Cloud was picked, from a select inside that very group."""
        [group] = [
            element for element in StructuredSyncConfig.as_form().to_formkit_form() if element.name == "confluence"
        ]

        assert group.condition_if == (
            "$: ($get(structured_source_kind).value === 'confluence') || "
            "($get(structured_source_kind).value === 'confluence' && $get(confluence_deployment).value === 'cloud')"
        )

    def test_retyping_the_spaces_keeps_the_state_and_a_new_space_resets_it(self):
        assert _config(api_token="a").scope_fingerprint() == _config(api_token="b").scope_fingerprint()
        assert _config(space_keys=["OPS", "ENG"]).scope_fingerprint() == _config().scope_fingerprint()
        assert _config(space_keys=["ENG"]).scope_fingerprint() != _config().scope_fingerprint()

    def test_the_kind_is_offered_by_its_name(self):
        assert ConfluenceAdapter.display_name.en == "Confluence"
