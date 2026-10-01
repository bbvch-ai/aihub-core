import pytest
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext
from swiss_ai_hub.core.form import ConfigSpecs
from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS  # noqa: F401 — rebuilds Group/Repeater
from swiss_ai_hub.core.form.elements.group import Group
from swiss_ai_hub.core.form.elements.select import Select

from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import (
    KIND_REF,
    AbstractStructuredSourceAdapter,
)
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.source_pipelines.tests.fake_structured_source_adapter import (
    FAKE_TRACKERS,
    FakeStructuredSyncConfig,
    FakeTrackerAdapter,
    fake_issue,
)


@pytest.fixture
def no_active_dlt_pipeline() -> None:
    """Outside a pipeline, dlt resolves an incremental cursor from whichever pipeline last ran in this process."""
    Container()[PipelineContext].deactivate()


def _config(**options) -> FakeStructuredSyncConfig:
    return FakeStructuredSyncConfig.model_validate(
        {
            "source_kind": "fake_tracker",
            "fake_tracker": {"base_url": "https://tracker.test", "api_token": "t-1", "project": "ABC", **options},
        }
    )


class TestAnnouncedForm:
    def test_the_shipped_pipeline_offers_no_kind_until_an_adapter_lands(self):
        elements = StructuredSyncConfig.as_form().to_formkit_form()

        assert [element.name for element in elements] == ["source_kind"]
        assert elements[0].options == []

    def test_each_kind_gets_one_group_shown_only_while_it_is_selected(self):
        elements = {element.name: element for element in FakeStructuredSyncConfig.as_form().to_formkit_form()}

        assert isinstance(elements["source_kind"], Select)
        assert elements["source_kind"].options == ["fake_tracker"]
        assert elements["source_kind"].ref == KIND_REF
        group = elements["fake_tracker"]
        assert isinstance(group, Group)
        assert group.condition_if == "$get(structured_source_kind).value === 'fake_tracker'"
        assert group.nullable is False

    def test_every_credential_of_a_kind_is_a_secret_path_derived_from_the_form(self):
        assert FakeStructuredSyncConfig.secret_field_paths() == {"fake_tracker.api_token"}

    def test_the_schema_accepts_a_submission_carrying_only_the_selected_kind(self):
        specs = ConfigSpecs.from_form(FakeStructuredSyncConfig.as_form(), "FakeStructuredSyncConfig")

        assert {"source_kind", "fake_tracker"} <= set(specs.config_schema["properties"])
        assert _config().options().project == "ABC"


class TestAdapter:
    def test_the_adapter_of_the_selected_kind_is_used(self):
        assert isinstance(_config().adapter(), FakeTrackerAdapter)

    def test_a_kind_this_pipeline_does_not_offer_is_refused(self):
        config = FakeStructuredSyncConfig.model_validate({"source_kind": "confluence"})

        with pytest.raises(ValueError, match="confluence"):
            config.adapter()

    @pytest.mark.usefixtures("no_active_dlt_pipeline")
    def test_records_carry_their_file_and_keep_every_field(self):
        """dlt applies the incremental cursor and de-duplicates by primary key after the mapping, so both must
        survive it."""
        FAKE_TRACKERS["https://tracker.test"] = [fake_issue("ABC", "ABC-1", "2026-09-01T10:00:00Z")]
        config = _config()

        [row] = list(config.adapter().file_source(config.options()))

        assert row["key"] == "ABC-1"
        assert row["updated"] == "2026-09-01T10:00:00Z"
        assert row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN] == "ABC/ABC-1.md"
        assert row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN].startswith("---\ntitle: Title of ABC-1\n")


class TestScopeFingerprint:
    def test_rotating_a_credential_keeps_the_cursors(self):
        assert _config(api_token="t-1").scope_fingerprint() == _config(api_token="t-2").scope_fingerprint()

    def test_changing_what_is_synced_reads_everything_again(self):
        """With the old cursor, issues of a newly added project older than it would never be fetched."""
        assert _config(project="ABC").scope_fingerprint() != _config(project="XYZ").scope_fingerprint()
