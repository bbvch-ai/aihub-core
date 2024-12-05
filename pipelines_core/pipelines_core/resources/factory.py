from typing import Dict

from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster_azure.adls2 import (
    ADLS2DefaultAzureCredential,
    ADLS2PickleIOManager,
    ADLS2Resource,
)
from lib_core.clients.DataLakeClientSingleton import DataLakeClientSingleton

from pipelines_core.io.AzureDataLakeIOManager import AzureDataLakeIOManager
from pipelines_core.io.DocStoreIOManager import DocStoreIOManager
from pipelines_core.io.VectorStoreIOManager import VectorStoreIOManager
from pipelines_core.resources.data_lake.DataLakeClientResource import (
    DataLakeClientResource,
)
from pipelines_core.resources.data_lake.DataLakeFileSystemResource import (
    DataLakeFileSystemResource,
)
from pipelines_core.resources.doc_store.MongoDocumentStoreResource import (
    MongoDocumentStoreResource,
)
from pipelines_core.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from pipelines_core.resources.llm.LanguageModelResource import LanguageModelResource
from pipelines_core.resources.llm.LlmHandlerResource import LlmHandlerResource
from pipelines_core.resources.organization.NamespaceResource import NamespaceResource
from pipelines_core.resources.vector_store.AzureAISearchVectorStoreResource import (
    AzureAISearchVectorStoreResource,
)


def namespace_resource(customer_name: str, namespace_name: str) -> NamespaceResource:
    return NamespaceResource(name=namespace_name, organization=customer_name)


def azure_data_lake_resources(
    namespace: NamespaceResource,
) -> Dict[str, ConfigurableResourceFactory]:
    data_lake_client = DataLakeClientResource(
        namespace=namespace,
    )
    data_lake_file_system = DataLakeFileSystemResource()
    data_lake_io_manager = AzureDataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
    }


def mongo_aisearch_storage_context_resources(
    namespace: NamespaceResource,
) -> Dict[str, ConfigurableResourceFactory]:
    vector_store = AzureAISearchVectorStoreResource(namespace=namespace)
    doc_store = MongoDocumentStoreResource(namespace=namespace)
    vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)
    doc_store_io_manager = DocStoreIOManager(doc_store=doc_store)
    return {
        "doc_store": doc_store,
        "vector_store": vector_store,
        "doc_store_io_manager": doc_store_io_manager,
        "vector_store_io_manager": vector_store_io_manager,
    }


def default_io_manager_azure_datalake_resources(
    namespace: NamespaceResource,
) -> Dict[str, ConfigurableResourceFactory]:
    adls2 = ADLS2Resource(
        storage_account=DataLakeClientSingleton().get_storage_account_name(),
        credential=ADLS2DefaultAzureCredential(kwargs={}),
    )
    adls2_pickle_io_manager = ADLS2PickleIOManager(
        adls2_file_system=namespace.organization,
        adls2_prefix=f".{namespace.name}-dagster/",
        adls2=adls2,
    )

    return {
        "adls2": adls2,
        "io_manager": adls2_pickle_io_manager,
    }


def default_llm_resources(
    namespace: NamespaceResource,
) -> Dict[str, ConfigurableResourceFactory]:
    llm_handler_resource = LlmHandlerResource(namespace=namespace)
    embedding_model_resource = EmbeddingModelResource(
        llm_handler_resource=llm_handler_resource,
        model_name="text-embedding-ada-002",
    )
    language_model = LanguageModelResource(
        llm_handler_resource=llm_handler_resource,
        model_name="gpt-4o-mini",
    )
    return {
        "llm_handler": llm_handler_resource,
        "embedding_model": embedding_model_resource,
        "language_model": language_model,
    }
