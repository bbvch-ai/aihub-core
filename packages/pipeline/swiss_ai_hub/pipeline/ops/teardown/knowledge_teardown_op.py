from dagster import Config, OpExecutionContext, ResourceParam, op

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.services.knowledge_teardown_service import KnowledgeTeardownService
from swiss_ai_hub.pipeline.util.bucket_utils import ensure_main_db_connection


class KnowledgeTeardownConfig(Config):
    """Per-run parameters for a namespace teardown, derived by the sensor from the flagged entity row.

    Everything the job needs already lives on the row, which is why the flag alone is the request and no
    event is published alongside it.
    """

    namespace_id: str
    namespace_name: str
    folder_name: str
    db_name: str


@op(description="Tears down one knowledge namespace across the data lake, the doc store and the vector store.")
def knowledge_teardown_op(
    context: OpExecutionContext,
    config: KnowledgeTeardownConfig,
    data_lake_client: ResourceParam[AbstractDataLakeClient],
) -> None:
    """Adapter around ``KnowledgeTeardownService``; the data lake client is the pipeline's own bucket-scoped one."""
    ensure_main_db_connection()

    context.log.info(f"Tearing down namespace '{config.namespace_name}' (folder '{config.folder_name}')")
    KnowledgeTeardownService.teardown_namespace(
        namespace_id=config.namespace_id,
        namespace_name=config.namespace_name,
        folder_name=config.folder_name,
        db_name=config.db_name,
        data_lake_client=data_lake_client,
    )
