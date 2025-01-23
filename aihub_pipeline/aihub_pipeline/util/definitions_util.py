from pathlib import Path
from typing import Sequence

from dagster import (
    AnchorBasedFilePathMapping,
    AssetsDefinition,
    Definitions,
    link_code_references_to_git,
    with_source_code_references,
)

from aihub_pipeline.assets.factories.documents_factory import documents_factory
from aihub_pipeline.assets.factories.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.observable_data_lake_factory import observable_data_lake_factory
from aihub_pipeline.assets.factories.removed_documents_factory import removed_documents_factory
from aihub_pipeline.executors.factory import default_process_executor
from aihub_pipeline.jobs.factory import observe_source_job
from aihub_pipeline.resources.factory import (
    azure_data_lake_resources,
    default_io_manager_azure_datalake_resources,
    default_llm_resources,
    mongo_aisearch_storage_context_resources,
    namespace_resource,
)
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource
from aihub_pipeline.schedules.factory import default_daily_materialize_schedule
from aihub_pipeline.sensors.factory import default_automation_sensor
from aihub_pipeline.util.key_utils import asset_key_from_customer_and_namespace
from aihub_pipeline.util.partition_utils import create_dynamic_partition


def asset_definition_with_code_link(
    assets: Sequence[AssetsDefinition], customer_name: str, namespace_name: str
) -> Sequence[AssetsDefinition]:
    return link_code_references_to_git(
        assets_defs=with_source_code_references(assets),
        git_url="https://github.com/bbvch-ai/ai-hub",
        git_branch="dev",
        file_path_mapping=AnchorBasedFilePathMapping(
            local_file_anchor=Path(__file__),
            file_anchor_path_in_repository=f"server/pipelines/customer/{customer_name}/{namespace_name}/__init__.py",
        ),
    )


def default_definitions(customer_name: str, namespace_name: str) -> Definitions:
    document_partitions = create_dynamic_partition(customer_name, namespace_name, "documents")

    DATA_LAKE_KEY = asset_key_from_customer_and_namespace(customer_name, namespace_name, "data_lake")
    DOCUMENT_KEY = asset_key_from_customer_and_namespace(customer_name, namespace_name, "documents")
    NODES_KEY = asset_key_from_customer_and_namespace(customer_name, namespace_name, "nodes")
    REMOVED_DOCUMENTS_KEY = asset_key_from_customer_and_namespace(customer_name, namespace_name, "removed_documents")

    observable_asset = observable_data_lake_factory(DATA_LAKE_KEY, document_partitions)

    assets = [
        observable_asset,
        removed_documents_factory(REMOVED_DOCUMENTS_KEY, data_lake_key=DATA_LAKE_KEY),
        documents_factory(DOCUMENT_KEY, data_lake_key=DATA_LAKE_KEY, partitions=document_partitions),
        nodes_factory(NODES_KEY, document_key=DOCUMENT_KEY, partitions=document_partitions),
    ]

    namespace = namespace_resource(customer_name, namespace_name)
    job = observe_source_job(
        observable_asset=observable_asset,
        customer_name=customer_name,
        namespace_name=namespace_name,
    )

    return Definitions(
        assets=asset_definition_with_code_link(assets, customer_name, namespace_name),
        resources={
            "namespace": namespace,
            "document_parser": DocumentParserResource(),
            "node_parser": MarkdownStructuralNodeParserResource(),
            **default_llm_resources(namespace),
            **default_io_manager_azure_datalake_resources(namespace),
            **mongo_aisearch_storage_context_resources(namespace),
            **azure_data_lake_resources(namespace),
        },
        sensors=[default_automation_sensor(assets)],
        executor=default_process_executor(),
        jobs=[job],
        schedules=[default_daily_materialize_schedule(job)],
    )
