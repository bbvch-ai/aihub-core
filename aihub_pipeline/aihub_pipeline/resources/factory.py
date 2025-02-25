from typing import Dict

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
    AzureOpenAIEmbeddingParameter,
)
from aihub_lib.infrastructure.azure.data_lake.DataLakeAccess import DataLakeAccess
from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster_azure.adls2 import ADLS2DefaultAzureCredential, ADLS2PickleIOManager, ADLS2Resource

from aihub_pipeline.io.AzureDataLakeIOManager import AzureDataLakeIOManager
from aihub_pipeline.io.DocStoreIOManager import DocStoreIOManager
from aihub_pipeline.io.VectorStoreIOManager import VectorStoreIOManager
from aihub_pipeline.resources.data_lake.DataLakeClientResource import DataLakeClientResource
from aihub_pipeline.resources.data_lake.DataLakeFileSystemResource import DataLakeFileSystemResource
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.resources.doc_store.DocStoreResource import DocStoreResource
from aihub_pipeline.resources.doc_store.MongoDocumentStoreResource import MongoDocumentStoreResource
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.resources.vector_store.AzureAISearchVectorStoreResource import AzureAISearchVectorStoreResource


def azure_data_lake_resources(container_name: str, directory_name: str) -> Dict[str, ConfigurableResourceFactory]:
    data_lake_client = DataLakeClientResource(container_name=container_name)
    data_lake_file_system = DataLakeFileSystemResource()
    data_lake_io_manager = AzureDataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    data_lake_resource = DataLakeResource(container_name=container_name, directory_name=directory_name)
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
        "data_lake_resource": data_lake_resource,
    }


def mongo_aisearch_storage_context_resources(
    vector_store_name: str,
    document_store_name: str,
    namespace_name: str,
) -> Dict[str, ConfigurableResourceFactory]:
    vector_store = AzureAISearchVectorStoreResource(vector_store_name=vector_store_name)
    doc_store = MongoDocumentStoreResource(document_store_name=document_store_name, namespace_name=namespace_name)
    vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)
    doc_store_io_manager = DocStoreIOManager(doc_store=doc_store)
    doc_store_resource = DocStoreResource(document_store_name=document_store_name, namespace_name=namespace_name)
    return {
        "doc_store": doc_store,
        "vector_store": vector_store,
        "doc_store_io_manager": doc_store_io_manager,
        "vector_store_io_manager": vector_store_io_manager,
        "doc_store_resource": doc_store_resource,
    }


def default_io_manager_azure_datalake_resources(
    container_name: str, directory_name: str
) -> Dict[str, ConfigurableResourceFactory]:
    adls2 = ADLS2Resource(
        storage_account=DataLakeAccess().get_storage_account_name(),
        credential=ADLS2DefaultAzureCredential(kwargs={}),
    )
    adls2_pickle_io_manager = ADLS2PickleIOManager(
        adls2_file_system=container_name,
        adls2_prefix=f".{directory_name}-dagster/",
        adls2=adls2,
    )

    return {
        "adls2": adls2,
        "io_manager": adls2_pickle_io_manager,
    }


def default_llm_resources() -> Dict[str, ConfigurableResourceFactory]:
    embedding_model_resource = EmbeddingModelResource(
        embedding_config=AzureOpenAIEmbeddingConfig(
            name="text-embedding-ada-002",
            base_url="https://aihub-dev-openai-che.openai.azure.com/",
            api_version="2023-12-01-preview",
            embedding_tokens_costs_per_thousand=0.000019,
            default_parameter=AzureOpenAIEmbeddingParameter(),
        )
    )
    language_model = LanguageModelResource(
        llm_config=AzureOpenAILLMConfig(
            name="gpt-4o-mini",
            base_url="https://aihub-dev-openai-che.openai.azure.com/",
            api_version="2023-12-01-preview",
            prompt_tokens_costs_per_thousand=0.00013599,
            completion_tokens_costs_per_thousand=0.0005440,
            default_parameter=AzureOpenAIParameter(temperature=0.0),
        )
    )
    return {
        "embedding_model": embedding_model_resource,
        "language_model": language_model,
    }
