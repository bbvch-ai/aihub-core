from typing import Annotated

from dagster import (
    AssetKey,
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.persistence import IngestorType

from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.observable_routed_data_lake_factory import (
    observable_routed_data_lake_factory,
)
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.removed_documents_factory import (
    removed_documents_factory,
)
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.routed_nodes_factory import routed_nodes_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.summary_nodes_factory import summary_nodes_factory
from swiss_ai_hub.pipeline.executors.factory import default_process_executor
from swiss_ai_hub.pipeline.io.routed_doc_store_io_manager import RoutedDocStoreIOManager
from swiss_ai_hub.pipeline.io.routed_s3_data_lake_io_manager import RoutedS3DataLakeIOManager
from swiss_ai_hub.pipeline.io.routed_vector_store_io_manager import RoutedVectorStoreIOManager
from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job, observe_source_job
from swiss_ai_hub.pipeline.resources.data_lake.s3.routed_s3_data_lake_client_resource import (
    RoutedS3DataLakeClientResource,
)
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_file_system_resource import S3DataLakeFileSystemResource
from swiss_ai_hub.pipeline.resources.doc_store.routed_doc_store_resource import RoutedDocStoreResource
from swiss_ai_hub.pipeline.resources.doc_store.routed_mongo_document_store_resource import (
    RoutedMongoDocumentStoreResource,
)
from swiss_ai_hub.pipeline.resources.factory import default_io_manager_s3_datalake_resources
from swiss_ai_hub.pipeline.resources.llm.embedding_model_resource import EmbeddingModelResource
from swiss_ai_hub.pipeline.resources.llm.language_model_resource import LanguageModelResource
from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource, LoaderType
from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)
from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import RecursiveSummaryParserResource
from swiss_ai_hub.pipeline.resources.parser.table_refinement_resource import TableRefinementResource
from swiss_ai_hub.pipeline.resources.vector_store.routed_milvus_vector_store_resource import (
    RoutedMilvusVectorStoreResource,
)
from swiss_ai_hub.pipeline.schedules.per_bucket_schedule import per_bucket_observe_schedule
from swiss_ai_hub.pipeline.sensors.factory import default_automation_sensor
from swiss_ai_hub.pipeline.sensors.nats.per_bucket_nats_document_uploaded_sensor import (
    per_bucket_nats_document_uploaded_sensor,
)
from swiss_ai_hub.pipeline.sensors.run_after_success_with_bucket_tag_sensor import (
    run_after_success_with_bucket_tag_sensor,
)
from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import run_failure_notification_sensors_from_settings

_DEFAULT_INGESTOR = IngestorType.RAG.value


def rag_pipeline_definitions(
    *,
    ingestor: Annotated[str, "Ingestor that owns the databases this pipeline serves"] = _DEFAULT_INGESTOR,
    embedding_model_name: Annotated[str, "LiteLLM model name for embeddings"] = "embedding/bge-m3",
    llm_model_name: Annotated[str, "LiteLLM model name for text generation"] = "text-generation/gemma-4-31B-it",
    with_summary_nodes: Annotated[bool, "Generate recursive summaries for hierarchical RAG"] = True,
    with_table_refinement: Annotated[bool, "Refine tables with LLM to detect structure and split"] = True,
    with_figure_descriptions: Annotated[bool, "Generate figure descriptions with vision LLM"] = True,
    observe_job_hour: Annotated[int, "Hour to run the daily per-bucket observation schedule"] = 0,
    observe_job_minute: Annotated[int, "Minute to run the daily per-bucket observation schedule"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
    document_parser_loader_type: Annotated[LoaderType, "Document parser loader type"] = LoaderType.MINERU,
    encode_partition_keys: Annotated[bool, "URL-encode file URIs inside composite partition keys"] = True,
) -> Definitions:
    """Single deployed pipeline that ingests every self-service knowledge database (Stage 2: data lake → vectors).

    Unlike ``default_definitions`` (one deployment per bucket), this pipeline is identity-free: its asset graph
    carries no bucket name, the target database is resolved per run (from the composite partition key on the
    partitioned write path, from the ``aihub/bucket`` run tag on the observe/remove path), and the per-bucket
    schedule + NATS sensor fan out over ``BucketEntity`` owned by ``ingestor`` at runtime. New databases need no
    code-location reload — only new partition keys and schedule/sensor fan-out.

    Every deployment-global name (asset keys, the dynamic-partition registry, job names, the Dagster
    intermediates prefix) is derived from ``ingestor``, because asset keys are unique per Dagster deployment and
    dynamic-partition registry names are global to the instance. That is what lets a second pipeline *type* be
    deployed alongside this one instead of colliding with it.
    """
    asset_group = f"{ingestor}_datalake_to_vectorstore"

    data_lake_key = AssetKey([asset_group, "data_lake"])
    document_key = AssetKey([asset_group, "documents"])
    nodes_key = AssetKey([asset_group, "nodes"])
    removed_documents_key = AssetKey([asset_group, "removed_documents"])

    document_partitions = DynamicPartitionsDefinition(name=f"{ingestor}_document_partitions")

    observable_asset = observable_routed_data_lake_factory(
        data_lake_key,
        document_partitions,
        max_partitions,
        encode_partition_keys=encode_partition_keys,
    )
    assets = [
        observable_asset,
        removed_documents_factory(removed_documents_key, data_lake_key=data_lake_key),
        documents_factory(
            document_key,
            data_lake_key=data_lake_key,
            partitions=document_partitions,
            enable_table_refinement=with_table_refinement,
            enable_figure_descriptions=with_figure_descriptions,
        ),
        routed_nodes_factory(nodes_key, document_key=document_key, partitions=document_partitions),
    ]
    if with_summary_nodes:
        summary_nodes_key = AssetKey([asset_group, "summary_nodes"])
        assets.append(
            summary_nodes_factory(
                summary_nodes_key, document_key=document_key, nodes_key=nodes_key, partitions=document_partitions
            )
        )

    observe_job = observe_source_job(observable_asset=observable_asset, source_location_name=ingestor)
    remove_job = materialize_asset_job(
        source_location_name=ingestor,
        job_name="remove_documents",
        asset_selection=AssetSelection.keys(removed_documents_key),
    )

    llm_config = LLMConfig(model_name=llm_model_name)
    embedding_config = EmbeddingModelConfig(model_name=embedding_model_name)

    resources: dict = {
        "document_parser": DocumentParserResource(loader_type=document_parser_loader_type),
        "node_parser": MarkdownStructuralNodeParserResource(llm_config=llm_config),
        "summary_parser": RecursiveSummaryParserResource(),
        "data_lake_io_manager": RoutedS3DataLakeIOManager(encode_partition_keys=encode_partition_keys),
        "doc_store_io_manager": RoutedDocStoreIOManager(encode_partition_keys=encode_partition_keys),
        "vector_store_io_manager": RoutedVectorStoreIOManager(encode_partition_keys=encode_partition_keys),
        "data_lake_client": RoutedS3DataLakeClientResource(),
        "data_lake_file_system": S3DataLakeFileSystemResource(),
        "doc_store": RoutedMongoDocumentStoreResource(),
        "doc_store_resource": RoutedDocStoreResource(),
        "vector_store": RoutedMilvusVectorStoreResource(),
        "embedding_model": EmbeddingModelResource(embedding_config=embedding_config),
        "language_model": LanguageModelResource(llm_config=llm_config),
        **default_io_manager_s3_datalake_resources(container_name=ingestor),
    }
    if with_table_refinement:
        resources["table_refinement"] = TableRefinementResource(llm_config=llm_config)

    return Definitions(
        assets=assets,
        resources=resources,
        sensors=[
            default_automation_sensor(assets),
            per_bucket_nats_document_uploaded_sensor(observe_job, ingestor=ingestor),
            run_after_success_with_bucket_tag_sensor(monitored_job=observe_job, triggered_job=remove_job),
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[
            per_bucket_observe_schedule(
                observe_job, ingestor=ingestor, hour=observe_job_hour, minute=observe_job_minute
            )
        ],
    )
