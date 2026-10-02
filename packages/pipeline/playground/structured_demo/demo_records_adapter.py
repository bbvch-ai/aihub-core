import json
from pathlib import Path
from typing import Any

import dlt
from dlt.extract import DltSource
from swiss_ai_hub.core.form import InputText
from swiss_ai_hub.core.i18n import LocaleString

from playground.structured_demo.demo_records_options import DemoRecordsOptions
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile


class DemoRecordsAdapter(AbstractStructuredSourceAdapter[DemoRecordsOptions]):
    """A structured source kind that reads its records from a local JSON file, for trying the pipeline end to end.

    Each record is ``{project, key, title, updated, status, body}``; ``project`` becomes the namespace. It is also
    the smallest working example of the adapter contract the Jira and Confluence adapters implement.
    """

    kind = "demo_records"

    @classmethod
    def options_form(cls) -> DemoRecordsOptions:
        return DemoRecordsOptions(
            file_path=InputText(
                label=LocaleString(en="Records file", de="Datensatzdatei"),
                help=LocaleString(en="JSON file inside the demo folder.", de="JSON-Datei im Demo-Ordner."),
                condition_if=cls.shown_for(cls.kind),
            )
        )

    def dlt_source(self, options: DemoRecordsOptions) -> DltSource:
        records_file = options.records_file()

        @dlt.source(name="demo_records")
        def demo_records():
            @dlt.resource(name="records", primary_key="key")
            def records(updated=dlt.sources.incremental("updated", initial_value="1970-01-01T00:00:00Z")):
                yield [record for record in self._read(records_file) if record["updated"] >= updated.last_value]

            return records

        return demo_records()

    def to_record_file(self, record: dict[str, Any]) -> StructuredRecordFile:
        return StructuredRecordFile(
            namespace=record["project"],
            path_segments=[record["key"]],
            frontmatter={
                "title": record["title"],
                "url": f"https://example.com/demo/{record['key']}",
                "updated": record["updated"],
                "status": record.get("status"),
            },
            body=record["body"],
        )

    def list_record_paths(self, options: DemoRecordsOptions) -> set[str]:
        return {
            StructuredRecordFile.object_key_for(record["project"], [record["key"]])
            for record in self._read(options.records_file())
        }

    @staticmethod
    def _read(records_file: Path) -> list[dict[str, Any]]:
        return json.loads(records_file.read_text())
