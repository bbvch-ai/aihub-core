"""A structured source kind for tests: an issue tracker whose records live in memory, keyed by base URL."""

from typing import Annotated, Any

import dlt
from dlt.extract import DltSource
from pydantic import Field
from swiss_ai_hub.core.form import Form, InputText, Password
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

FAKE_TRACKERS: dict[str, list[dict[str, Any]]] = {}


def fake_issue(project: str, key: str, updated: str, body: str = "Body text") -> dict[str, Any]:
    return {"project": project, "key": key, "title": f"Title of {key}", "updated": updated, "body": body}


class FakeTrackerOptions(Form):
    base_url: Annotated[str | InputText, Field(description="Tracker URL; selects the in-memory records.")] = ""
    api_token: Annotated[str | Password, Field(description="Token, a secret.")] = ""
    project: Annotated[str | InputText, Field(description="Project to sync, part of the scope.")] = ""


class FakeTrackerAdapter(AbstractStructuredSourceAdapter[FakeTrackerOptions]):
    kind = "fake_tracker"

    @classmethod
    def options_form(cls) -> FakeTrackerOptions:
        shown = cls.shown_for(cls.kind)
        return FakeTrackerOptions(
            base_url=InputText(label=LocaleString(en="Base URL"), condition_if=shown),
            api_token=Password(label=LocaleString(en="API token"), condition_if=shown),
            project=InputText(label=LocaleString(en="Project"), condition_if=shown),
        )

    def dlt_source(self, options: FakeTrackerOptions) -> DltSource:
        records = FAKE_TRACKERS[options.base_url]

        @dlt.source(name="fake_tracker")
        def fake_tracker():
            @dlt.resource(name="issues", primary_key="key")
            def issues(updated=dlt.sources.incremental("updated", initial_value="1970-01-01T00:00:00Z")):
                yield [record for record in records if record["updated"] >= updated.last_value]

            return issues

        return fake_tracker()

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile:
        return StructuredRecordFile(
            namespace=record["project"],
            path_segments=[record["key"]],
            frontmatter={"title": record["title"], "url": f"https://tracker.test/{record['key']}"},
            body=record["body"],
        )

    def list_record_paths(self, options: FakeTrackerOptions) -> set[str]:
        return {
            StructuredRecordFile.object_key_for(record["project"], [record["key"]])
            for record in FAKE_TRACKERS[options.base_url]
        }


class FakeStructuredSyncConfig(StructuredSyncConfig):
    fake_tracker: Annotated[FakeTrackerOptions, Field(description="Fake tracker options.")] = Field(
        default_factory=FakeTrackerOptions
    )

    @classmethod
    def adapters(cls) -> list[type[AbstractStructuredSourceAdapter]]:
        return [FakeTrackerAdapter]
