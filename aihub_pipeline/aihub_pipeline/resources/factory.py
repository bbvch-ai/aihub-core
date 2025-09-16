from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.azure.data_lake.DataLakeAccess import DataLakeAccess
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings
from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster_aws.s3 import S3PickleIOManager, S3Resource
from dagster_azure.adls2 import ADLS2DefaultAzureCredential, ADLS2PickleIOManager, ADLS2Resource

from aihub_pipeline.io.AzureDataLakeIOManager import AzureDataLakeIOManager
from aihub_pipeline.io.DocStoreIOManager import DocStoreIOManager
from aihub_pipeline.io.S3DataLakeIOManager import S3DataLakeIOManager
from aihub_pipeline.io.VectorStoreIOManager import VectorStoreIOManager
from aihub_pipeline.resources.data_lake.azure.AzureDataLakeClientResource import AzureDataLakeClientResource
from aihub_pipeline.resources.data_lake.azure.AzureDataLakeFileSystemResource import AzureDataLakeFileSystemResource
from aihub_pipeline.resources.data_lake.DataLakeResource import DataLakeResource
from aihub_pipeline.resources.data_lake.s3.S3DataLakeClientResource import S3DataLakeClientResource
from aihub_pipeline.resources.data_lake.s3.S3DataLakeFileSystemResource import S3DataLakeFileSystemResource
from aihub_pipeline.resources.doc_store.DocStoreResource import DocStoreResource
from aihub_pipeline.resources.doc_store.MongoDocumentStoreResource import MongoDocumentStoreResource
from aihub_pipeline.resources.llm.EmbeddingModelResource import EmbeddingModelResource
from aihub_pipeline.resources.llm.LanguageModelResource import LanguageModelResource
from aihub_pipeline.resources.vector_store.MilvusVectorStoreResource import MilvusVectorStoreResource


def azure_data_lake_resources(
    container_name: str, figures_directory_name: str
) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for Azure Data Lake resources."""
    data_lake_client = AzureDataLakeClientResource(container_name=container_name)
    data_lake_file_system = AzureDataLakeFileSystemResource()
    data_lake_io_manager = AzureDataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    data_lake_resource = DataLakeResource(container_name=container_name, figures_directory_name=figures_directory_name)
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
        "data_lake_resource": data_lake_resource,
    }


def s3_data_lake_resources(container_name: str, figures_directory_name: str) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for S3 Data Lake resources (MinIO)."""
    data_lake_client = S3DataLakeClientResource(container_name=container_name)
    data_lake_file_system = S3DataLakeFileSystemResource()
    data_lake_io_manager = S3DataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    data_lake_resource = DataLakeResource(container_name=container_name, figures_directory_name=figures_directory_name)
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
        "data_lake_resource": data_lake_resource,
    }


def mongo_document_store_resource(
    document_store_name: str,
) -> dict[str, ConfigurableResourceFactory]:
    doc_store = MongoDocumentStoreResource(document_store_name=document_store_name)
    doc_store_io_manager = DocStoreIOManager(doc_store=doc_store)
    doc_store_resource = DocStoreResource(document_store_name=document_store_name)
    return {
        "doc_store": doc_store,
        "doc_store_io_manager": doc_store_io_manager,
        "doc_store_resource": doc_store_resource,
    }


def milvus_vector_store_resource(
    vector_store_uri: str,
    vector_store_name: str,
    dimensions: int = 3072,
) -> dict[str, ConfigurableResourceFactory]:
    vector_store = MilvusVectorStoreResource(
        uri=vector_store_uri, collection_name=vector_store_name, embedding_vector_dimension=dimensions
    )
    vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)
    return {
        "vector_store": vector_store,
        "vector_store_io_manager": vector_store_io_manager,
    }


def local_mongo_milvus_storage_context_resource(
    vector_store_uri: str,
    store_name: str,
    dimensions: int = 3072,
) -> dict[str, ConfigurableResourceFactory]:
    return {
        **mongo_document_store_resource(document_store_name=store_name),
        **milvus_vector_store_resource(
            vector_store_uri=vector_store_uri, vector_store_name=store_name, dimensions=dimensions
        ),
    }


def default_io_manager_azure_datalake_resources(
    container_name: str, directory_name: str
) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for Azure default IO manager resources."""
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


def default_io_manager_s3_datalake_resources(container_name: str) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for S3 default IO manager resources (MinIO)."""
    s3_config = S3StorageSettings()

    s3_resource = S3Resource(
        aws_access_key_id=s3_config.ACCESS_KEY,
        aws_secret_access_key=s3_config.SECRET_KEY.get_secret_value(),
        endpoint_url=s3_config.ENDPOINT,
        region_name=s3_config.REGION,
    )
    s3_pickle_io_manager = S3PickleIOManager(
        s3_resource=s3_resource,
        s3_bucket=container_name,
        s3_prefix=f".{container_name}-dagster/",
    )

    return {
        "s3": s3_resource,
        "io_manager": s3_pickle_io_manager,
    }


def default_llm_resources() -> dict[str, ConfigurableResourceFactory]:
    embedding_model_resource = EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(model_name="azure/text-embedding-ada-002")
    )
    language_model = LanguageModelResource(llm_config=LLMConfig(model_name="azure/gpt-4o-mini"))
    return {
        "embedding_model": embedding_model_resource,
        "language_model": language_model,
    }
