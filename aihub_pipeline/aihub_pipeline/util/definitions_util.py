from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.milvus.MilvusSettings import MilvusSettings
from aihub_lib.nats.topic_managers.pipeline.PipelineInstanceTopicManager import PipelineInstanceTopicManager
from dagster import (
    AnchorBasedFilePathMapping,
    AssetKey,
    AssetsDefinition,
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
    link_code_references_to_git,
    with_source_code_references,
)

from aihub_pipeline.assets.factories.data_lake_to_vector_store.documents_factory import documents_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.data_lake_to_vector_store.observable_data_lake_factory import (
    observable_data_lake_factory,
)
from aihub_pipeline.assets.factories.data_lake_to_vector_store.removed_documents_factory import (
    removed_documents_factory,
)
from aihub_pipeline.assets.factories.data_lake_to_vector_store.summary_nodes_factory import summary_nodes_factory
from aihub_pipeline.assets.factories.local_files_system_to_data_lake.observable_local_file_system_factory import (
    observable_local_file_system_factory,
)
from aihub_pipeline.assets.factories.share_point_to_data_lake.observable_share_point_factory import (
    observable_share_point_factory,
)
from aihub_pipeline.assets.factories.source_to_data_lake.data_lake_file_factory import data_lake_file_factory
from aihub_pipeline.assets.factories.source_to_data_lake.placeholder_refdocs_factory import placeholder_refdocs_factory
from aihub_pipeline.assets.factories.source_to_data_lake.removed_data_lake_files_factory import (
    removed_data_lake_files_factory,
)
from aihub_pipeline.const.pipeline_names import INTERNAL_DATALAKE, INTERNAL_KNOWLEDGE_DB
from aihub_pipeline.executors.factory import default_process_executor
from aihub_pipeline.io.LocalFileSystemIOManager import LocalFileSystemIOManager
from aihub_pipeline.io.SharePointIOManager import SharePointIoManager
from aihub_pipeline.jobs.factory import materialize_asset_job, observe_source_job
from aihub_pipeline.resources.factory import (
    default_io_manager_s3_datalake_resources,
    local_mongo_milvus_storage_context_resource,
    mongo_document_store_resource,
    s3_data_lake_resources,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.resources.local_file_system.LocalFileSystemResource import LocalFileSystemResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource
from aihub_pipeline.resources.parser.RecursiveSummaryParserResource import RecursiveSummaryParserResource
from aihub_pipeline.resources.parser.TableRefinementResource import TableRefinementResource
from aihub_pipeline.resources.share_point.SharePointResource import SharePointResource
from aihub_pipeline.schedules.factory import daily_schedule_at
from aihub_pipeline.sensors.factory import default_automation_sensor
from aihub_pipeline.sensors.nats.nats_document_uploaded_sensor import nats_document_uploaded_sensor
from aihub_pipeline.util.bucket_utils import get_db_name_from_bucket_name


def asset_definition_with_code_link(
    assets: Sequence[AssetsDefinition], customer_name: str, datalake_container_name: str
) -> Sequence[AssetsDefinition]:
    return link_code_references_to_git(
        assets_defs=with_source_code_references(assets),
        git_url=f"https://github.com/bbvch-ai/aihub-{customer_name}",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository=f"pipelines/{datalake_container_name}/__init__.py",
        ),
    )


def default_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where raw documents are stored"],
    embedding_model_name: Annotated[str, "LiteLLM model name for embeddings"] = "embedding/large",
    llm_model_name: Annotated[str, "LiteLLM model name for text generation"] = "text-generation/mini",
    with_summary_nodes: Annotated[bool, "Generate recursive summaries for hierarchical RAG"] = True,
    with_table_refinement: Annotated[bool, "Refine tables with LLM to detect structure and split"] = True,
    with_figure_descriptions: Annotated[bool, "Generate figure descriptions with vision LLM"] = True,
    auto_sync: Annotated[bool, "Whether the S3 bucket is auto-synced (i.e. with local fs pipeline)"] = False,
    observe_job_hour: Annotated[int, "Hour to run daily data lake observation job"] = 2,
    observe_job_minute: Annotated[int, "Minute to run daily data lake observation job"] = 0,
    remove_job_hour: Annotated[int, "Hour to run daily removed documents cleanup job"] = 3,
    remove_job_minute: Annotated[int, "Minute to run daily removed documents cleanup job"] = 0,
    vector_store_dimensions: Annotated[int | None, "Embedding vector dimensions must match model"] = None,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
    document_parser_loader_type: Annotated[LoaderType, "Document parser loader type"] = LoaderType.DOCLING,
) -> Definitions:
    """
    Creates a complete DataLake to vector store pipeline using local resources.

    Use this when you have documents in S3 and want to prepare them for RAG applications.
    The pipeline processes raw files into searchable embeddings stored in local Mongo and Milvus.

    Pipeline: S3 → Document Processing → Mongo → Node Chunking → Summary Generation → Milvus
    """
    document_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_document_partitions")

    data_lake_key = AssetKey([datalake_container_name, "datalake_to_vectorstore", "data_lake"])
    document_key = AssetKey([datalake_container_name, "datalake_to_vectorstore", "documents"])
    nodes_key = AssetKey([datalake_container_name, "datalake_to_vectorstore", "nodes"])
    removed_documents_key = AssetKey([datalake_container_name, "datalake_to_vectorstore", "removed_documents"])

    observable_asset = observable_data_lake_factory(data_lake_key, document_partitions, max_partitions)
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
        summary_nodes_key = AssetKey([datalake_container_name, "datalake_to_vectorstore", "summary_nodes"])
        assets.append(
            summary_nodes_factory(
                summary_nodes_key, document_key=document_key, nodes_key=nodes_key, partitions=document_partitions
            )
        )

    job = observe_source_job(
        observable_asset=observable_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_documents",
        asset_selection=AssetSelection.keys(removed_documents_key),
    )

    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=auto_sync)
    llm_config = LLMConfig(model_name=llm_model_name)
    embedding_config = EmbeddingModelConfig(model_name=embedding_model_name)
    milvus_settings = MilvusSettings()
    dimensions = vector_store_dimensions if vector_store_dimensions is not None else milvus_settings.DIMENSION

    resources: dict = {
        "document_parser": DocumentParserResource(loader_type=document_parser_loader_type),
        "node_parser": MarkdownStructuralNodeParserResource(llm_config=llm_config),
        "summary_parser": RecursiveSummaryParserResource(),
        **default_io_manager_s3_datalake_resources(container_name=datalake_container_name),
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri=milvus_settings.URL, store_name=store_name, dimensions=dimensions
        ),
        **s3_data_lake_resources(
            container_name=datalake_container_name,
        ),
        "embedding_model": EmbeddingModelResource(
            embedding_config=embedding_config,
        ),
        "language_model": LanguageModelResource(llm_config=llm_config),
    }

    if with_table_refinement:
        resources["table_refinement"] = TableRefinementResource(llm_config=llm_config)

    return Definitions(
        assets=assets,
        resources=resources,
        sensors=[
            default_automation_sensor(assets),
            nats_document_uploaded_sensor(
                job=job,
                topic_manager=PipelineInstanceTopicManager(
                    source_type=INTERNAL_DATALAKE,
                    source_id=datalake_container_name,
                    target_type=INTERNAL_KNOWLEDGE_DB,
                    target_id=store_name,
                ),
            ),
        ],
        executor=default_process_executor(),
        jobs=[job, remove_job],
        schedules=[
            daily_schedule_at(job, hour=observe_job_hour, minute=observe_job_minute),
            daily_schedule_at(remove_job, hour=remove_job_hour, minute=remove_job_minute),
        ],
    )


def default_sharepoint_to_datalake_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where SharePoint files will be uploaded"],
    datalake_directory_name: Annotated[str | None, "Optional subdirectory within container"] = None,
    target_folders: Annotated[list[str] | None, "List of SharePoint folder paths to sync"] = None,
    exclude_folders: Annotated[list[str] | None, "List of SharePoint folder paths to exclude"] = None,
    supported_filetypes: Annotated[list[str] | None, "List of file extensions to sync"] = None,
    observe_job_hour: Annotated[int, "Hour to run daily SharePoint observation job"] = 0,
    observe_job_minute: Annotated[int, "Minute to run daily SharePoint observation job"] = 0,
    remove_job_hour: Annotated[int, "Hour to run daily removed files cleanup job"] = 1,
    remove_job_minute: Annotated[int, "Minute to run daily removed files cleanup job"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
) -> Definitions:
    """
    Creates a SharePoint to DataLake pipeline using local S3-compatible storage.

    Use this when you need to sync corporate documents from SharePoint to your local data lake.
    The pipeline monitors SharePoint for changes and automatically downloads new/updated files
    to your local S3 storage. It handles authentication, filtering, and cleanup of deleted files.

    Pipeline: SharePoint → S3

    This is the first step - combine with default_definitions() to process files into
    embeddings for RAG applications.
    """
    sharepoint_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_sharepoint_partitions")

    sharepoint_key = AssetKey([datalake_container_name, "sharepoint_to_datalake", "sharepoint"])
    data_lake_files_key = AssetKey([datalake_container_name, "sharepoint_to_datalake", "data_lake_files"])
    placeholder_refdocs_key = AssetKey([datalake_container_name, "sharepoint_to_datalake", "placeholder_refdocs"])
    removed_data_lake_files_key = AssetKey(
        [datalake_container_name, "sharepoint_to_datalake", "removed_data_lake_files"]
    )

    observable_sharepoint_asset = observable_share_point_factory(sharepoint_key, sharepoint_partitions, max_partitions)

    assets = [
        observable_sharepoint_asset,
        data_lake_file_factory(
            key=data_lake_files_key,
            source_key=sharepoint_key,
            partitions=sharepoint_partitions,
        ),
        placeholder_refdocs_factory(
            key=placeholder_refdocs_key,
            data_lake_files_key=data_lake_files_key,
            partitions=sharepoint_partitions,
        ),
        removed_data_lake_files_factory(
            key=removed_data_lake_files_key,
            source_key=sharepoint_key,
        ),
    ]

    observe_job = observe_source_job(
        observable_asset=observable_sharepoint_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_sharepoint_files",
        asset_selection=AssetSelection.keys(removed_data_lake_files_key),
    )

    sharepoint_client = SharePointResource(
        target_folders=target_folders,
        exclude_folders=exclude_folders,
        supported_filetypes=supported_filetypes,
    )

    sharepoint_io_manager = SharePointIoManager(share_point_client=sharepoint_client)

    # Get the store name for MongoDB (auto_sync=False for SharePoint pipelines)
    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=False)

    return Definitions(
        assets=assets,
        resources={
            "share_point_client": sharepoint_client,
            "sharepoint_io_manager": sharepoint_io_manager,
            **s3_data_lake_resources(
                container_name=datalake_container_name,
                directory_name=datalake_directory_name,
            ),
            **mongo_document_store_resource(document_store_name=store_name),
        },
        sensors=[default_automation_sensor(assets)],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[
            daily_schedule_at(observe_job, hour=observe_job_hour, minute=observe_job_minute),
            daily_schedule_at(remove_job, hour=remove_job_hour, minute=remove_job_minute),
        ],
    )


def default_local_filesystem_to_datalake_definitions(
    *,
    datalake_container_name: Annotated[str, "S3 bucket/container name where local filesystem files will be uploaded"],
    base_path: Annotated[str, "Root directory path to scan for files"],
    include_patterns: Annotated[list[str] | None, "List of patterns to include"] = None,
    datalake_directory_name: Annotated[str | None, "Optional subdirectory within container"] = None,
    exclude_patterns: Annotated[list[str] | None, "List of patterns to exclude"] = None,
    observe_job_hour: Annotated[int, "Hour to run daily filesystem observation job"] = 0,
    observe_job_minute: Annotated[int, "Minute to run daily filesystem observation job"] = 0,
    remove_job_hour: Annotated[int, "Hour to run daily removed files cleanup job"] = 1,
    remove_job_minute: Annotated[int, "Minute to run daily removed files cleanup job"] = 0,
    max_partitions: Annotated[int, "Maximum number of partitions to create or delete at once"] = 1000,
) -> Definitions:
    """
    Creates a Local File System to DataLake pipeline using S3-compatible storage.

    Use this when you need to sync files from a local or network file system to your data lake.
    The pipeline monitors specified directories for changes and automatically uploads new/updated files
    to your S3 storage. It handles flexible pattern-based file filtering, folder organization,
    and cleanup of deleted files.

    All filtering uses regex patterns for maximum flexibility. Use helper functions from
    aihub_pipeline.util.pattern_utils to convert lists to patterns:
    - exact_match_pattern(["A", "B"]) for exact folder names
    - extension_pattern([".pdf", ".docx"]) for file extensions
    - contains_pattern("archive") for substring matching

    Pipeline: Local File System → S3

    This is the first step - combine with default_definitions() to process files into
    embeddings for RAG applications.
    """
    filesystem_partitions = DynamicPartitionsDefinition(name=f"{datalake_container_name}_local_fs_partitions")

    filesystem_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "local_fs"])
    data_lake_files_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "data_lake_files"])
    placeholder_refdocs_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "placeholder_refdocs"])
    removed_data_lake_files_key = AssetKey([datalake_container_name, "local_fs_to_datalake", "removed_data_lake_files"])

    observable_filesystem_asset = observable_local_file_system_factory(
        filesystem_key,
        filesystem_partitions,
        max_partitions,
    )

    assets = [
        observable_filesystem_asset,
        data_lake_file_factory(
            key=data_lake_files_key,
            source_key=filesystem_key,
            partitions=filesystem_partitions,
        ),
        placeholder_refdocs_factory(
            key=placeholder_refdocs_key,
            data_lake_files_key=data_lake_files_key,
            partitions=filesystem_partitions,
        ),
        removed_data_lake_files_factory(
            key=removed_data_lake_files_key,
            source_key=filesystem_key,
        ),
    ]

    observe_job = observe_source_job(
        observable_asset=observable_filesystem_asset,
        source_location_name=datalake_container_name,
    )

    remove_job = materialize_asset_job(
        source_location_name=datalake_container_name,
        job_name="remove_filesystem_files",
        asset_selection=AssetSelection.keys(removed_data_lake_files_key),
    )

    filesystem_client = LocalFileSystemResource(
        base_path=base_path,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns,
    )

    filesystem_io_manager = LocalFileSystemIOManager(local_file_system_client=filesystem_client)

    # Get the store name for MongoDB (auto_sync=True for local filesystem pipelines)
    store_name = get_db_name_from_bucket_name(bucket_name=datalake_container_name, auto_sync=True)

    return Definitions(
        assets=assets,
        resources={
            "local_file_system_client": filesystem_client,
            "local_file_system_io_manager": filesystem_io_manager,
            **s3_data_lake_resources(
                container_name=datalake_container_name,
                directory_name=datalake_directory_name,
            ),
            **mongo_document_store_resource(document_store_name=store_name),
        },
        sensors=[default_automation_sensor(assets)],
        executor=default_process_executor(),
        jobs=[observe_job, remove_job],
        schedules=[
            daily_schedule_at(observe_job, hour=observe_job_hour, minute=observe_job_minute),
            daily_schedule_at(remove_job, hour=remove_job_hour, minute=remove_job_minute),
        ],
    )
