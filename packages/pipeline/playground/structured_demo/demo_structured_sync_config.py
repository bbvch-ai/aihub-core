from typing import Annotated

from pydantic import Field

from playground.structured_demo.demo_records_adapter import DemoRecordsAdapter
from playground.structured_demo.demo_records_options import DemoRecordsOptions
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig


class DemoStructuredSyncConfig(StructuredSyncConfig):
    """The structured source form offering the demo kind: what a kind needs is its options field and its adapter."""

    demo_records: Annotated[DemoRecordsOptions, Field(description="Demo records options.")] = Field(
        default_factory=DemoRecordsOptions
    )

    @classmethod
    def adapters(cls) -> list[type[AbstractStructuredSourceAdapter]]:
        return [DemoRecordsAdapter]
