from typing import Annotated

from dagster import OpDefinition, OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.types.structured_listing import StructuredListing
from swiss_ai_hub.pipeline.types.structured_sync_outcome import StructuredSyncOutcome
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_run_tag
from swiss_ai_hub.pipeline.util.source_builders import source_config_for_bucket


def list_structured_record_paths_op(
    source: Annotated[str, "Source pipeline id this code location runs as"],
    config_type: Annotated[type[StructuredSyncConfig], "Config class a database's source configuration is read as"],
) -> OpDefinition:
    """The step that lists every record the database's source currently has, after the sync wrote its changes.

    It takes the sync's outcome as input so it can only run after it: a record written by the sync but missing from an
    earlier listing would be removed and never fetched again.
    """

    @op(name=f"{source}_list_structured_record_paths", code_version="v1")
    def list_structured_record_paths(
        context: OpExecutionContext, outcome: StructuredSyncOutcome
    ) -> Output[StructuredListing]:
        bucket = bucket_from_run_tag(context)
        config = source_config_for_bucket(bucket, source, config_type)
        if config.scope_fingerprint() != outcome.scope_fingerprint:
            raise ValueError(
                f"The source configuration of '{bucket}' changed during the run; nothing is removed, and the next run "
                "reads the new scope from the start."
            )
        listed = sorted(config.adapter().list_record_paths(config.options()))
        return Output(
            StructuredListing(listed_keys=listed, written_keys=outcome.written_keys),
            metadata={"Records at the source": len(listed)},
        )

    return list_structured_record_paths
