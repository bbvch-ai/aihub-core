from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from dagster import AssetKey, Definitions, DynamicPartitionsDefinition

from aihub_pipeline.assets.factories.documents_factory import documents_factory
from aihub_pipeline.assets.factories.nodes_factory import nodes_factory
from aihub_pipeline.assets.factories.observable_data_lake_factory import observable_data_lake_factory
from aihub_pipeline.assets.factories.removed_documents_factory import removed_documents_factory
from aihub_pipeline.assets.factories.summary_nodes_factory import summary_nodes_factory
from aihub_pipeline.executors.factory import default_process_executor
from aihub_pipeline.resources.factory import (
    azure_data_lake_resources,
    default_io_manager_azure_datalake_resources,
    local_mongo_milvus_storage_context_resource,
)
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.resources.parser.DocumentParserResource import DocumentParserResource, LoaderType
from aihub_pipeline.resources.parser.MarkdownStructuralNodeParserResource import MarkdownStructuralNodeParserResource
from aihub_pipeline.resources.parser.RecursiveSummaryParserResource import RecursiveSummaryParserResource
from aihub_pipeline.sensors.factory import default_automation_sensor

DATA_LAKE_KEY = AssetKey(["playground", "data_lake"])
DOCUMENT_KEY = AssetKey(["playground", "documents"])
NODES_KEY = AssetKey(["playground", "nodes"])
REMOVED_DOCUMENTS_KEY = AssetKey(["playground", "removed_documents"])
SUMMARY_NODES_KEY = AssetKey(["playground", "summary_nodes"])

DATALAKE_CONTAINER_NAME = "playground"
DATALAKE_DIRECTORY_NAME = "test"
FIGURES_DIRECTORY_NAME = "__figures__"
NAMESPACE_NAME = "test"
STORE_NAME = "test"

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


defs = Definitions(
    assets=assets,
    resources={
        **default_io_manager_azure_datalake_resources(
            container_name=DATALAKE_CONTAINER_NAME, directory_name=DATALAKE_DIRECTORY_NAME
        ),
        "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
        "node_parser": MarkdownStructuralNodeParserResource(),
        "summary_parser": RecursiveSummaryParserResource(),
        **local_mongo_milvus_storage_context_resource(
            vector_store_uri="http://localhost:19530",
            store_name=STORE_NAME,
            namespace_name=NAMESPACE_NAME,
        ),
        **azure_data_lake_resources(
            container_name=DATALAKE_CONTAINER_NAME,
            directory_name=DATALAKE_DIRECTORY_NAME,
            figures_directory_name=FIGURES_DIRECTORY_NAME,
        ),
        "embedding_model": EmbeddingModelResource(
            embedding_config=AzureOpenAIEmbeddingConfig(
                name="text-embedding-3-large",
                base_url="https://bbvaihub-openai-sui.openai.azure.com/",
                api_version="2023-05-15",
                embedding_tokens_costs_per_thousand=0.000118,
                default_parameter=AzureOpenAIEmbeddingParameter(),
            ),
        ),
        "language_model": LanguageModelResource(
            llm_config=AzureOpenAILLMConfig(
                name="gpt-4o-mini",
                base_url="https://bbvaihub-openai-sui.openai.azure.com/",
                api_version="2024-12-01-preview",
                prompt_tokens_costs_per_thousand=0.00013599,
                completion_tokens_costs_per_thousand=0.0005440,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            )
        ),
    },
    sensors=[default_automation_sensor(assets)],
    executor=default_process_executor(),
)
