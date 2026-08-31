from typing import Annotated

from dagster import (
    AssetKey,
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.persistence import IngestorEntity, IngestorType

from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.removed_documents_factory import (
    removed_documents_factory,
)
from swiss_ai_hub.pipeline.assets.factories.data_lake_to_vector_store.summary_nodes_factory import summary_nodes_factory
from swiss_ai_hub.pipeline.executors.factory import default_process_executor
from swiss_ai_hub.pipeline.io.routed_doc_store_io_manager import RoutedDocStoreIOManager
from swiss_ai_hub.pipeline.io.routed_s3_data_lake_io_manager import RoutedS3DataLakeIOManager
from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager
from swiss_ai_hub.pipeline.jobs.factory import materialize_asset_job, observe_source_job
from swiss_ai_hub.pipeline.jobs.knowledge_teardown_job import knowledge_teardown_job
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_file_system_resource import S3DataLakeFileSystemResource
from swiss_ai_hub.pipeline.resources.factory import default_io_manager_s3_datalake_resources
from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource, LoaderType
from swiss_ai_hub.pipeline.resources.parser.markdown_structural_node_parser_resource import (
    MarkdownStructuralNodeParserResource,
)
from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import RecursiveSummaryParserResource
from swiss_ai_hub.pipeline.resources.parser.table_refinement_resource import TableRefinementResource
from swiss_ai_hub.pipeline.schedules.per_bucket_schedule import per_bucket_observe_schedule
from swiss_ai_hub.pipeline.sensors.factory import default_automation_sensor
from swiss_ai_hub.pipeline.sensors.ingestor_registration_sensor import ingestor_registration_sensor
from swiss_ai_hub.pipeline.sensors.knowledge_teardown_sensor import knowledge_teardown_sensor
from swiss_ai_hub.pipeline.sensors.nats.nats_document_uploaded_sensor import (
    nats_document_uploaded_sensor,
)
from swiss_ai_hub.pipeline.sensors.run_after_success_sensor import run_after_success_sensor
from swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor import run_failure_notification_sensors_from_settings

_DEFAULT_INGESTOR = IngestorType.DOCUMENT_INGESTION.value


def document_ingestion_pipeline_definitions(
    *,
    ingestor: Annotated[str, "Ingestor that owns the databases this pipeline serves"] = _DEFAULT_INGESTOR,
    display_name: Annotated[LocaleString | None, "Localized name of a custom ingestor, shown in the UI"] = None,
    description: Annotated[LocaleString | None, "Localized description of a custom ingestor"] = None,
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

    observable_asset = observable_data_lake_factory(
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
        nodes_factory(nodes_key, document_key=document_key, partitions=document_partitions),
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
    teardown_job = knowledge_teardown_job(source_location_name=ingestor)

    registration_sensors = _registration_sensors(ingestor, display_name, description)

    # Deployment defaults. A database that names its own models overrides these per run; these are what a
    # database created before models were configurable keeps using.
    llm_config = LLMConfig(model_name=llm_model_name)
    embedding_config = EmbeddingModelConfig(model_name=embedding_model_name)

    resources: dict = {
        "document_parser": DocumentParserResource(loader_type=document_parser_loader_type),
        "node_parser": MarkdownStructuralNodeParserResource(llm_config=llm_config, embedding_config=embedding_config),
        "summary_parser": RecursiveSummaryParserResource(llm_config=llm_config),
        "data_lake_io_manager": RoutedS3DataLakeIOManager(encode_partition_keys=encode_partition_keys),
        "doc_store_io_manager": RoutedDocStoreIOManager(encode_partition_keys=encode_partition_keys),
        "vector_store_io_manager": VectorStoreIOManager(encode_partition_keys=encode_partition_keys),
        "data_lake_file_system": S3DataLakeFileSystemResource(),
        **default_io_manager_s3_datalake_resources(container_name=ingestor),
    }
    if with_table_refinement:
        resources["table_refinement"] = TableRefinementResource(llm_config=llm_config)

    return Definitions(
        assets=assets,
        resources=resources,
        sensors=[
            default_automation_sensor(assets),
            nats_document_uploaded_sensor(observe_job, ingestor=ingestor),
            knowledge_teardown_sensor(teardown_job, ingestor=ingestor),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job, require_bucket_tag=True),
            *registration_sensors,
            *run_failure_notification_sensors_from_settings(),
        ],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job, teardown_job],
        schedules=[
            per_bucket_observe_schedule(
                observe_job, ingestor=ingestor, hour=observe_job_hour, minute=observe_job_minute
            )
        ],
    )


def _registration_sensors(
    ingestor: str,
    display_name: LocaleString | None,
    description: LocaleString | None,
) -> list:
    """The self-registration sensor, for a custom ingestor only.

    The platform's own ingestors are already in ``IngestorType`` and localized by the API, so they need
    no row. A custom one is unknown to the API until this pipeline advertises it — and unlabelled it
    could only ever render as a bare id in the selector, so its labels are required rather than optional.
    """
    if ingestor in {ingestor_type.value for ingestor_type in IngestorType}:
        return []
    if ingestor in IngestorEntity.reserved_ids():
        msg = f"Ingestor '{ingestor}' is reserved by the platform and cannot be claimed by a pipeline."
        raise ValueError(msg)
    if display_name is None or description is None:
        msg = f"Custom ingestor '{ingestor}' needs a display_name and a description to be selectable."
        raise ValueError(msg)
    return [ingestor_registration_sensor(ingestor, display_name, description)]
