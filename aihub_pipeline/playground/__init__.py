from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from dagster import AssetKey, AssetSelection, Definitions, DynamicPartitionsDefinition
from mongoengine import disconnect

from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)
from aihub_pipeline.assets.factories.data_lake_to_vector_store.removed_documents_factory import (
    removed_documents_factory,
)
from aihub_pipeline.assets.factories.data_lake_to_vector_store.summary_nodes_factory import summary_nodes_factory
from aihub_pipeline.executors.factory import default_process_executor
from aihub_pipeline.jobs.factory import materialize_asset_job, observe_source_job
from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource
from aihub_pipeline.resources.parser.RecursiveSummaryParserResource import RecursiveSummaryParserResource
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor
from aihub_pipeline.util.bucket_utils import get_db_name_from_bucket_name
from aihub_pipeline.util.connection_utils import connect_to_mongo_db

# Configuration: Change this to switch between cloud providers
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])
NODES_KEY = AssetKey(["playground", "nodes"])
REMOVED_DOCUMENTS_KEY = AssetKey(["playground", "removed_documents"])
SUMMARY_NODES_KEY = AssetKey(["playground", "summary_nodes"])

DATALAKE_CONTAINER_NAME = "playground"
DATALAKE_DIRECTORY_NAME = "test"
NAMESPACE_NAME = DATALAKE_DIRECTORY_NAME
STORE_NAME = DATALAKE_CONTAINER_NAME
FIGURES_DIRECTORY_NAME = "__figures__"


def get_store_name() -> str:
    connect_to_mongo_db(AIHubSettings().MONGO_MAIN_DB_NAME)
    try:
        return get_db_name_from_bucket_name(DATALAKE_CONTAINER_NAME)
    finally:
        disconnect()


document_partitions = DynamicPartitionsDefinition(name="document_partitions")

observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
assets = [
    observable_asset,
    removed_documents_factory(REMOVED_DOCUMENTS_KEY, data_lake_key=DATA_LAKE_KEY),
    documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions),
    nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions),
    summary_nodes_factory(
        SUMMARY_NODES_KEY, document_key=DOCUMENT_KEY, nodes_key=NODES_KEY, partitions=document_partitions
    ),
]

job = observe_source_job(
    observable_asset=observable_asset,
    source_location_name=NAMESPACE_NAME,
)

remove_job = materialize_asset_job(
    source_location_name=NAMESPACE_NAME,
    job_name="remove_documents",
    asset_selection=AssetSelection.keys(REMOVED_DOCUMENTS_KEY),
)

defs = Definitions(
    assets=assets,
    resources={
        **default_io_manager_s3_datalake_resources(container_name=DATALAKE_CONTAINER_NAME),
        "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING, include_images=True),
        "node_parser": MarkdownStructuralNodeParserResource(),
        "summary_parser": RecursiveSummaryParserResource(),
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name=get_store_name(),
        ),
        **s3_data_lake_resources(
            container_name=DATALAKE_CONTAINER_NAME,
            figures_directory_name=FIGURES_DIRECTORY_NAME,
        ),
        "embedding_model": EmbeddingModelResource(
            embedding_config=EmbeddingModelConfig(model_name="azure/text-embedding-3-large"),
        ),
        "language_model": LanguageModelResource(llm_config=LLMConfig(model_name="azure/gpt-4o-mini")),
    },
    sensors=[default_automation_sensor(assets)],
    executor=default_process_executor(),
    jobs=[job, remove_job],
    schedules=[daily_schedule_at(job, hour=0, minute=0), daily_schedule_at(remove_job, hour=1, minute=0)],
)
