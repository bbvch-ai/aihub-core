"""A structured source kind for tests: an issue tracker whose records and attachments live in memory, keyed by base
URL."""

import hashlib
from collections.abc import Iterator
from typing import Annotated, Any

import dlt
from dlt.extract import DltResource, DltSource
from pydantic import Field
from swiss_ai_hub.core.form import Form, InputText, Password
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_file_unavailable_error import StructuredFileUnavailableError
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.types.structured_file_reference import StructuredFileReference
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile

FAKE_TRACKERS: dict[str, list[dict[str, Any]]] = {}
FAKE_ATTACHMENTS: dict[str, dict[str, bytes | None]] = {}
"""Per tracker URL, each attachment's name and content; None for one the tracker lists but refuses to serve."""
FAKE_DOWNLOADS: list[str] = []


def fake_issue(project: str, key: str, updated: str, body: str = "Body text") -> dict[str, Any]:
    return {"project": project, "key": key, "title": f"Title of {key}", "updated": updated, "body": body}


class FakeTrackerOptions(Form):
    base_url: Annotated[str | InputText, Field(description="Tracker URL; selects the in-memory records.")] = ""
    api_token: Annotated[str | Password, Field(description="Token, a secret.")] = ""
    project: Annotated[str | InputText, Field(description="Project to sync, part of the scope.")] = ""


class FakeTrackerAdapter(AbstractStructuredSourceAdapter[FakeTrackerOptions]):
    kind = "fake_tracker"
    display_name = LocaleString(en="Fake tracker")

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
        def fake_tracker() -> list[DltResource]:
            @dlt.resource(name="issues", primary_key="key")
            def issues(
                updated: dlt.sources.incremental[str] = dlt.sources.incremental(
                    "updated", initial_value="1970-01-01T00:00:00Z"
                ),
            ) -> Iterator[list[dict[str, Any]]]:
                yield [record for record in records if record["updated"] >= updated.last_value]

            @dlt.resource(name="attachments", primary_key="name")
            def attachments() -> Iterator[list[dict[str, Any]]]:
                seen: dict[str, str] = dlt.current.resource_state().setdefault(self.FILES_SEEN, {})
                current = {self._attachment(name, content) for name, content in self._attachments(options)}
                changed = [reference for reference in current if seen.get(reference[0]) != reference[1]]
                seen.clear()
                seen.update(dict(current))
                if changed:
                    yield [
                        {"name": key.split("/", 1)[1], "checksum": checksum, "base_url": options.base_url}
                        for key, checksum in changed
                    ]

            return [issues, attachments]

        return fake_tracker()

    def read_file(self, options: FakeTrackerOptions, reference: StructuredFileReference) -> bytes:
        FAKE_DOWNLOADS.append(reference.download_url)
        name = reference.download_url.rsplit("/", 1)[1]
        content = FAKE_ATTACHMENTS[options.base_url][name]
        if content is None:
            raise StructuredFileUnavailableError(f"{name} is forbidden")
        return content

    @staticmethod
    def _attachments(options: FakeTrackerOptions) -> list[tuple[str, bytes | None]]:
        return list(FAKE_ATTACHMENTS.get(options.base_url, {}).items())

    @staticmethod
    def _attachment(name: str, content: bytes | None) -> tuple[str, str]:
        checksum = hashlib.sha1(content or b"", usedforsecurity=False).hexdigest()
        return FakeTrackerAdapter.attachment_key(name), checksum

    @staticmethod
    def attachment_key(name: str) -> str:
        stem, extension = name.rsplit(".", 1)
        return StructuredRecordFile.object_key_for("Attachments", [stem], extension)

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile | StructuredFileReference:
        if "checksum" in record:
            stem, extension = record["name"].rsplit(".", 1)
            return StructuredFileReference(
                namespace="Attachments",
                path_segments=[stem],
                extension=extension,
                download_url=f"{record['base_url']}/files/{record['name']}",
                size=0,
                title=record["name"],
                url=f"{record['base_url']}/attachments/{record['name']}",
            )
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
        } | {self.attachment_key(name) for name, _ in self._attachments(options)}


class FakeStructuredSyncConfig(StructuredSyncConfig):
    fake_tracker: Annotated[FakeTrackerOptions, Field(description="Fake tracker options.")] = Field(
        default_factory=FakeTrackerOptions
    )

    @classmethod
    def adapters(cls) -> list[type[AbstractStructuredSourceAdapter]]:
        return [FakeTrackerAdapter]
