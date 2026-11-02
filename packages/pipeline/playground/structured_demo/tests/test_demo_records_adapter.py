import pytest
from dlt.common.configuration.container import Container
from dlt.common.pipeline import PipelineContext

from playground.structured_demo.demo_records_options import DemoRecordsOptions
from playground.structured_demo.demo_structured_sync_config import DemoStructuredSyncConfig
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter


def _config(file_path: str = "demo_records.json") -> DemoStructuredSyncConfig:
    return DemoStructuredSyncConfig.model_validate(
        {"source_kind": "demo_records", "demo_records": {"file_path": file_path}}
    )


class TestDemoRecords:
    def test_the_sample_lists_every_record_under_its_project(self):
        config = _config()

        assert config.adapter().list_record_paths(config.options()) == {
            "ONBOARDING/ONB-1.md",
            "ONBOARDING/ONB-2.md",
            "SUPPORT/SUP-7.md",
        }

    def test_each_sample_record_becomes_markdown_with_its_fields_in_frontmatter(self):
        Container()[PipelineContext].deactivate()
        config = _config()

        rows = {
            row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]: row
            for row in config.adapter().file_source(config.options())
        }

        markdown = rows["SUPPORT/SUP-7.md"][AbstractStructuredSourceAdapter.MARKDOWN_COLUMN]
        assert markdown.startswith("---\nstatus: Open\ntitle: Password reset takes too long\n")
        assert markdown.endswith("The mail relay queue is suspected.\n")

    @pytest.mark.parametrize("escape", ["../../../../.env", "/etc/passwd", "tests/../../demo_records.json/../../x"])
    def test_a_file_outside_the_demo_folder_is_refused(self, escape: str):
        """Whoever creates a database picks the path; it must not read the container's own files."""
        with pytest.raises(ValueError, match="only reads files inside"):
            DemoRecordsOptions(file_path=escape).records_file()

    def test_the_demo_offers_its_kind_in_the_form(self):
        elements = {element.name: element for element in DemoStructuredSyncConfig.as_form().to_formkit_form()}

        [option] = elements["source_kind"].options
        assert (option["value"], option["label"].en) == ("demo_records", "Demo records")
        assert elements["demo_records"].condition_if == "$get(structured_source_kind).value === 'demo_records'"
