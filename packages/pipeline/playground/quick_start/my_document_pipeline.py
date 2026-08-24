from dagster import AssetKey, Definitions, DynamicPartitionsDefinition
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.infrastructure import AIHubSettings
from swiss_ai_hub.core.topic_managers import PipelineInstanceTopicManager

# Import AI-Hub pipeline factories
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)
from swiss_ai_hub.pipeline.const.pipeline_names import INTERNAL_DATALAKE, INTERNAL_KNOWLEDGE_DB
from swiss_ai_hub.pipeline.jobs.factory import observe_source_job

# Import AI-Hub resources and utilities
from swiss_ai_hub.pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    s3_data_lake_resources,
)
from swiss_ai_hub.pipeline.resources.llm.embedding_model_resource import EmbeddingModelResource
from swiss_ai_hub.pipeline.resources.llm.language_model_resource import LanguageModelResource
from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource, LoaderType
from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)
from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import RecursiveSummaryParserResource
from swiss_ai_hub.pipeline.schedules.factory import daily_schedule_at
from swiss_ai_hub.pipeline.sensors.factory import default_automation_sensor
from swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor import nats_document_uploaded_sensor
from swiss_ai_hub.pipeline.util.bucket_utils import get_db_name_from_bucket_name

# Pipeline configuration
DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])
NODES_KEY = AssetKey(["playground", "nodes"])

CONTAINER_NAME = AIHubSettings().DEFAULT_BUCKET_NAME

# LLM configuration for document parsing and node processing
llm_config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

# The node parser needs this too, to cap nodes at the embedding model's input limit
embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")

# Dynamic partitions for scalable document processing
document_partitions = DynamicPartitionsDefinition(name="document_partitions")

# Create the pipeline assets using AI-Hub factories
observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions, max_partitions=1000)

assets = [
    # Observable asset watches the data lake for new/changed documents
    observable_asset,
    # Document factory processes raw files into RefDocs with metadata
    documents_factory(
        DOCUMENT_KEY,
        data_lake_key=DATA_LAKE_KEY,
        partitions=document_partitions,
        enable_table_refinement=True,
        enable_figure_descriptions=True,
    ),
    # Nodes factory chunks documents into searchable nodes with embeddings
    nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions),
]
# Define the job to observe the data lake and trigger processing
observe_job = observe_source_job(
    observable_asset=observable_asset,
    source_location_name=CONTAINER_NAME,
)

# Define the complete pipeline
defs = Definitions(
    assets=assets,
    resources={
        # Data lake I/O managers for S3-compatible storage
        **default_io_manager_s3_datalake_resources(container_name=CONTAINER_NAME),
        # Document processing resources
        "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),
        "node_parser": MarkdownStructuralNodeParserResource(llm_config=llm_config, embedding_config=embedding_config),
        "summary_parser": RecursiveSummaryParserResource(llm_config=llm_config),
        # Vector store and document store (MongoDB + Milvus)
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name=get_db_name_from_bucket_name(bucket_name=CONTAINER_NAME, auto_sync=False),
        ),
        # Data lake resources for file management
        **s3_data_lake_resources(
            container_name=CONTAINER_NAME,
        ),
        # AI models for embeddings and summaries
        "embedding_model": EmbeddingModelResource(
            embedding_config=embedding_config,
        ),
        "language_model": LanguageModelResource(llm_config=llm_config),
    },
    # Add jobs for pipeline operations
    jobs=[observe_job],
    # Add scheduling - observe daily at midnight
    schedules=[daily_schedule_at(observe_job, hour=0, minute=0)],
    # Add sensors for automation and nats observation
    sensors=[
        default_automation_sensor(assets),
        nats_document_uploaded_sensor(
            job=observe_job,
            topic_manager=PipelineInstanceTopicManager(
                source_type=INTERNAL_DATALAKE,
                source_id=CONTAINER_NAME,
                target_type=INTERNAL_KNOWLEDGE_DB,
                target_id=CONTAINER_NAME,
            ),
        ),
    ],
)
