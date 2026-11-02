"""A structured source pipeline with a demo kind, for trying the sync end to end on the dev stack.

Run it next to the ingestion pipeline with ``make structured-demo``. It registers as ``structured_demo``, so it never
touches databases of the shipped ``structured`` source.
"""

from swiss_ai_hub.core.i18n import LocaleString

from playground.structured_demo.demo_structured_sync_config import DemoStructuredSyncConfig
from swiss_ai_hub.pipeline.util.structured_pipeline_definitions_util import structured_pipeline_definitions

defs = structured_pipeline_definitions(
    source="structured_demo",
    display_name=LocaleString(en="Demo records (JSON file)", de="Demo-Datensätze (JSON-Datei)"),
    description=LocaleString(
        en="Syncs records from a JSON file in the playground, to try the structured source pipeline.",
        de="Synchronisiert Datensätze aus einer JSON-Datei im Playground, um die Pipeline auszuprobieren.",
    ),
    config=DemoStructuredSyncConfig.as_form(),
)
