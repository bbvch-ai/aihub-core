from dagster import ConfigurableResource, InitResourceContext

from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_resource_init
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client


class RoutedS3DataLakeClientResource(ConfigurableResource[S3DataLakeClient]):
    """Per-run S3 data lake client for the RAG pipeline, scoped to the run's bucket.

    Unlike ``S3DataLakeClientResource`` (fixed ``container_name``), this resolves the bucket from the
    ``aihub/bucket`` run tag, so a single deployed code location serves every self-service database. Used
    on the tagged observe/remove path (``fetch_all_files``, ``delete_figures_for_many_ref_doc``); the
    partitioned write path resolves S3 from the composite partition key in the routed IO manager instead.
    """

    ensure_bucket: bool = True

    def create_resource(self, context: InitResourceContext) -> S3DataLakeClient:
        bucket = bucket_from_resource_init(context)
        return build_s3_data_lake_client(bucket, ensure_bucket=self.ensure_bucket)
