from collections.abc import Sequence

from dagster import AssetKey, AssetSelection, define_asset_job
from dagster._core.definitions.unresolved_asset_job_definition import UnresolvedAssetJobDefinition


def retry_failed_ingestion_job(
    *, source_location_name: str, asset_keys: Sequence[AssetKey]
) -> UnresolvedAssetJobDefinition:
    """The partitioned job the retry sensor launches; each run selects only the one asset that failed.

    It carries no run priority of its own: each retry is requested below the default, so it never queues ahead of a
    file that was just uploaded or an observation that authorizes new ingestion.
    """
    return define_asset_job(
        name=f"{source_location_name}_retry_failed_ingestion",
        selection=AssetSelection.assets(*asset_keys),
        description="Ingests a document again whose latest ingestion attempt failed.",
    )
