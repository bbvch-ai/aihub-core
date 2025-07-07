from collections.abc import Sequence
from pathlib import Path

from dagster import (
    AnchorBasedFilePathMapping,
    AssetKey,
    AssetsDefinition,
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
from aihub_pipeline.executors.factory import default_process_executor
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.resources.factory import (
    azure_data_lake_resources,
    default_io_manager_azure_datalake_resources,
    default_llm_resources,
    mongo_aisearch_storage_context_resources,
)
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource
from aihub_pipeline.schedules.factory import default_daily_materialize_schedule
from aihub_pipeline.sensors.factory import default_automation_sensor


def asset_definition_with_code_link(
    assets: Sequence[AssetsDefinition], customer_name: str, namespace_name: str
) -> Sequence[AssetsDefinition]:
    return link_code_references_to_git(
        assets_defs=with_source_code_references(assets),
        git_url=f"https://github.com/bbvch-ai/aihub-{customer_name}",
        git_branch="main",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository=f"pipelines/{namespace_name}/__init__.py",
        ),
    )


def default_definitions(
    datalake_container_name: str,
    namespace_name: str,
    datalake_directory_name: str,
    vector_store_name: str,
    document_store_name: str,
    dimensions: int = 3072,
) -> Definitions:
    document_partitions = DynamicPartitionsDefinition(name="document_partitions")

    DATA_LAKE_KEY = AssetKey([namespace_name, "data_lake"])
    DOCUMENT_KEY = AssetKey([namespace_name, "documents"])
    NODES_KEY = AssetKey([namespace_name, "nodes"])
    REMOVED_DOCUMENTS_KEY = AssetKey([namespace_name, "removed_documents"])

    observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)
    assets = [
        observable_asset,
        removed_documents_factory(REMOVED_DOCUMENTS_KEY, data_lake_key=DATA_LAKE_KEY),
        documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions),
        nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions),
    ]

    job = observe_source_job(
        observable_asset=observable_asset,
        namespace_name=namespace_name,
    )

    return Definitions(
        assets=assets,
        resources={
            "document_parser": DocumentParserResource(),
            "node_parser": MarkdownStructuralNodeParserResource(),
            **default_llm_resources(),
            **default_io_manager_azure_datalake_resources(
                container_name=datalake_container_name, directory_name=datalake_directory_name
            ),
            **mongo_aisearch_storage_context_resources(
                vector_store_name=vector_store_name,
                document_store_name=document_store_name,
                namespace_name=namespace_name,
                dimensions=dimensions,
            ),
            **azure_data_lake_resources(container_name=datalake_container_name, directory_name=datalake_directory_name),
        },
        sensors=[default_automation_sensor(assets)],
        executor=default_process_executor(),
        jobs=[job],
        schedules=[default_daily_materialize_schedule(job)],
    )
