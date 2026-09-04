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
from swiss_ai_hub.core.ingestors import IngestorConfig
from swiss_ai_hub.core.persistence import Ingestor, IngestorEntity, IngestorType

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
from swiss_ai_hub.pipeline.ingestors.document_ingestion_config import DocumentIngestionConfig
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
    display_name: Annotated[LocaleString | None, "Localized name shown in the create-database selector"] = None,
    description: Annotated[LocaleString | None, "Localized description of what the pipeline does"] = None,
    config: Annotated[IngestorConfig | None, "Form-mode config announced for this ingestor's databases"] = None,
    embedding_model_name: Annotated[
        str, "Default LiteLLM embedding model, per database overridable"
    ] = "embedding/bge-m3",
    llm_model_name: Annotated[
        str, "Default LiteLLM text-generation model, per database overridable"
    ] = "text-generation/gemma-4-31B-it",
    vision_model_name: Annotated[str | None, "Default figure-description model; the text model when None"] = None,
    with_summary_nodes: Annotated[bool, "Default for recursive summaries, per database overridable"] = True,
    with_table_refinement: Annotated[bool, "Default for LLM table refinement, per database overridable"] = True,
    with_figure_descriptions: Annotated[bool, "Default for figure descriptions, per database overridable"] = True,
    observe_job_hour: Annotated[int, "Hour to run the daily per-bucket observation schedule"] = 0,
    observe_job_minute: Annotated[int, "Minute to run the daily per-bucket observation schedule"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
    document_parser_loader_type: Annotated[LoaderType, "Document parser loader type"] = LoaderType.MINERU,
    encode_partition_keys: Annotated[bool, "URL-encode file URIs inside composite partition keys"] = True,
) -> Definitions:
    """Single deployed pipeline that ingests every self-service knowledge database (Stage 2: data lake → vectors).

    Unlike the frozen legacy pipelines (one deployment per bucket), this pipeline is identity-free: its asset graph
    carries no bucket name, the target database is resolved per run (from the composite partition key on the
    partitioned write path, from the ``aihub/bucket`` run tag on the observe/remove path), and the per-bucket
    schedule + NATS sensor fan out over ``BucketEntity`` owned by ``ingestor`` at runtime. New databases need no
    code-location reload — only new partition keys and schedule/sensor fan-out.

    Every deployment-global name (asset keys, the dynamic-partition registry, job names, the Dagster
    intermediates prefix) is derived from ``ingestor``, because asset keys are unique per Dagster deployment and
    dynamic-partition registry names are global to the instance. That is what lets a second pipeline *type* be
    deployed alongside this one instead of colliding with it.

    The models and enrichment flags are *deployment defaults*: they pre-fill the form this pipeline announces
    (``config``) and are what a database that stores no value of its own falls back to at run time. The asset
    graph is the same for every database; each enrichment op decides per run from the bucket's configuration.
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
        documents_factory(document_key, data_lake_key=data_lake_key, partitions=document_partitions),
        nodes_factory(nodes_key, document_key=document_key, partitions=document_partitions),
        summary_nodes_factory(
            AssetKey([asset_group, "summary_nodes"]),
            document_key=document_key,
            nodes_key=nodes_key,
            partitions=document_partitions,
        ),
    ]

    observe_job = observe_source_job(observable_asset=observable_asset, source_location_name=ingestor)
    remove_job = materialize_asset_job(
        source_location_name=ingestor,
        job_name="remove_documents",
        asset_selection=AssetSelection.keys(removed_documents_key),
    )
    teardown_job = knowledge_teardown_job(source_location_name=ingestor)

    announced_config = config or DocumentIngestionConfig.as_form(
        llm_model=llm_model_name,
        embedding_model=embedding_model_name,
        vision_model=vision_model_name,
        with_summary_nodes=with_summary_nodes,
        with_table_refinement=with_table_refinement,
        with_figure_descriptions=with_figure_descriptions,
    )
    registration_sensor = _registration_sensor(ingestor, display_name, description, announced_config)

    llm_config = LLMConfig(model_name=llm_model_name)
    embedding_config = EmbeddingModelConfig(model_name=embedding_model_name)

    resources: dict = {
        "document_parser": DocumentParserResource(loader_type=document_parser_loader_type),
        "node_parser": MarkdownStructuralNodeParserResource(llm_config=llm_config, embedding_config=embedding_config),
        "summary_parser": RecursiveSummaryParserResource(),
        "data_lake_io_manager": RoutedS3DataLakeIOManager(encode_partition_keys=encode_partition_keys),
        "doc_store_io_manager": RoutedDocStoreIOManager(encode_partition_keys=encode_partition_keys),
        "vector_store_io_manager": VectorStoreIOManager(encode_partition_keys=encode_partition_keys),
        "data_lake_file_system": S3DataLakeFileSystemResource(),
        "table_refinement": TableRefinementResource(),
        **default_io_manager_s3_datalake_resources(container_name=ingestor),
    }

    return Definitions(
        assets=assets,
        resources=resources,
        sensors=[
            default_automation_sensor(assets),
            nats_document_uploaded_sensor(observe_job, ingestor=ingestor),
            knowledge_teardown_sensor(teardown_job, ingestor=ingestor),
            run_after_success_sensor(monitored_job=observe_job, triggered_job=remove_job, require_bucket_tag=True),
            registration_sensor,
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


def _registration_sensor(
    ingestor: str,
    display_name: LocaleString | None,
    description: LocaleString | None,
    config: IngestorConfig,
):
    """The self-registration sensor that announces this pipeline's labels, form and schema to the API.

    The shipped pipeline registers like any custom one — the API learns what it can offer, and how a database of
    it is configured, from the record alone. Only the shipped ingestor may leave the labels out, since the
    platform carries translations for it; a custom one unlabelled could only ever render as a bare id.
    """
    if ingestor in IngestorEntity.reserved_ids():
        msg = f"Ingestor '{ingestor}' is reserved by the platform and cannot be claimed by a pipeline."
        raise ValueError(msg)
    if ingestor == IngestorType.DOCUMENT_INGESTION.value:
        display_name = display_name or LocaleString.from_i18n_path("lib.ingestors.document_ingestion.display_name")
        description = description or LocaleString.from_i18n_path("lib.ingestors.document_ingestion.description")
    if display_name is None or description is None:
        msg = f"Custom ingestor '{ingestor}' needs a display_name and a description to be selectable."
        raise ValueError(msg)
    return ingestor_registration_sensor(Ingestor.from_config(ingestor, display_name, description, config))
