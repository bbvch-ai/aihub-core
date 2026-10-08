from typing import Annotated

from dagster import AssetKey, AssetsDefinition, graph_asset

from swiss_ai_hub.pipeline.ops.source.routed.announce_removed_files import announce_removed_files
from swiss_ai_hub.pipeline.ops.source.routed.delete_data_lake_files_from_bucket import (
    delete_data_lake_files_from_bucket,
)
from swiss_ai_hub.pipeline.ops.structured.list_structured_record_paths import list_structured_record_paths_op
from swiss_ai_hub.pipeline.ops.structured.reconcile_structured_bucket import reconcile_structured_bucket_op
from swiss_ai_hub.pipeline.ops.structured.sync_structured_records import sync_structured_records_op
from swiss_ai_hub.pipeline.source_pipelines.structured_sync_config import StructuredSyncConfig
from swiss_ai_hub.pipeline.util.key_utils import group_name_from_asset_key


def structured_sync_factory(
    key: AssetKey,
    *,
    source: Annotated[str, "Source pipeline id this code location runs as"],
    config_type: Annotated[type[StructuredSyncConfig], "Config class a database's source configuration is read as"],
) -> AssetsDefinition:
    """One sync of the database the run's ``aihub/bucket`` tag names: write what changed, then remove what is gone.

    Sync, listing and removal are steps of one asset rather than assets of their own: values handed between steps are
    stored per run, while an asset's value is stored under its key, which every database shares. The asset's own
    value, the removed URIs, is stored that way and read by nobody. Build it once per code location, since Dagster
    refuses two steps of the same name.
    """
    sync = sync_structured_records_op(source, config_type, key)
    list_record_paths = list_structured_record_paths_op(source, config_type)
    reconcile = reconcile_structured_bucket_op(source)

    @graph_asset(
        key=key,
        group_name=group_name_from_asset_key(key),
        description="Syncs the knowledge database this run targets from its structured source (routed by run tag).",
    )
    def structured_records() -> list[str]:
        return announce_removed_files(delete_data_lake_files_from_bucket(reconcile(list_record_paths(sync()))))

    return structured_records
