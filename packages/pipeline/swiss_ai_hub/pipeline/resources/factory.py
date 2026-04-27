from dagster._config.pythonic_config import ConfigurableResourceFactory
from dagster_aws.s3 import S3PickleIOManager, S3Resource
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.infrastructure import MilvusSettings, S3StorageSettings
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import MilvusIndexType

from swiss_ai_hub.pipeline.io.azure_data_lake_io_manager import AzureDataLakeIOManager
from swiss_ai_hub.pipeline.io.doc_store_io_manager import DocStoreIOManager
from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager
from swiss_ai_hub.pipeline.resources.data_lake.azure.azure_data_lake_client_resource import AzureDataLakeClientResource
from swiss_ai_hub.pipeline.resources.data_lake.azure.azure_data_lake_file_system_resource import (
    AzureDataLakeFileSystemResource,
)
from swiss_ai_hub.pipeline.resources.data_lake.data_lake_resource import DataLakeResource
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client_resource import S3DataLakeClientResource
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_file_system_resource import S3DataLakeFileSystemResource
from swiss_ai_hub.pipeline.resources.doc_store.doc_store_resource import DocStoreResource
from swiss_ai_hub.pipeline.resources.doc_store.mongo_document_store_resource import MongoDocumentStoreResource
from swiss_ai_hub.pipeline.resources.llm.embedding_model_resource import EmbeddingModelResource
from swiss_ai_hub.pipeline.resources.llm.language_model_resource import LanguageModelResource
from swiss_ai_hub.pipeline.resources.vector_store.milvus_vector_store_resource import MilvusVectorStoreResource


def azure_data_lake_resources(
    container_name: str,
    directory_name: str | None = None,
) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for Azure Data Lake resources."""
    data_lake_client = AzureDataLakeClientResource(container_name=container_name)
    data_lake_file_system = AzureDataLakeFileSystemResource()
    data_lake_io_manager = AzureDataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
    )
    data_lake_resource = DataLakeResource(
        container_name=container_name,
        directory_name=directory_name,
    )
    return {
        "data_lake_client": data_lake_client,
        "data_lake_file_system": data_lake_file_system,
        "data_lake_io_manager": data_lake_io_manager,
        "data_lake_resource": data_lake_resource,
    }


def s3_data_lake_resources(
    container_name: str,
    directory_name: str | None = None,
    encode_partition_keys: bool = False,
) -> dict[str, ConfigurableResourceFactory]:
    """Factory function for S3 Data Lake resources (MinIO)."""
    data_lake_client = S3DataLakeClientResource(container_name=container_name)
    data_lake_file_system = S3DataLakeFileSystemResource()
    data_lake_io_manager = S3DataLakeIOManager(
        data_lake_client=data_lake_client,
        data_lake_file_system=data_lake_file_system,
        encode_partition_keys=encode_partition_keys,
    )
    data_lake_resource = DataLakeResource(
        container_name=container_name,
        directory_name=directory_name,
    )
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
    dimensions: int,
    index_type: MilvusIndexType = MilvusIndexType.HNSW,
) -> dict[str, ConfigurableResourceFactory]:
    milvus_settings = MilvusSettings()
    vector_store = MilvusVectorStoreResource(
        uri=vector_store_uri,
        collection_name=vector_store_name,
        embedding_vector_dimension=dimensions,
        index_type=index_type,
        token=milvus_settings.get_token(),
    )
    vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)
    return {
        "vector_store": vector_store,
        "vector_store_io_manager": vector_store_io_manager,
    }


def local_mongo_milvus_storage_context_resource(
    vector_store_uri: str,
    store_name: str,
    dimensions: int,
) -> dict[str, ConfigurableResourceFactory]:
    return {
        **mongo_document_store_resource(document_store_name=store_name),
        **milvus_vector_store_resource(
            vector_store_uri=vector_store_uri, vector_store_name=store_name, dimensions=dimensions
        ),
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
    op_intermediates_io_manager = S3PickleIOManager(
        s3_resource=s3_resource,
        s3_bucket="dagster",
        s3_prefix=f"{container_name}/",
    )

    return {
        "s3": s3_resource,
        "io_manager": op_intermediates_io_manager,
    }


def default_llm_resources() -> dict[str, ConfigurableResourceFactory]:
    embedding_model_resource = EmbeddingModelResource(
        embedding_config=EmbeddingModelConfig(model_name="embedding/bge-m3")
    )
    language_model = LanguageModelResource(llm_config=LLMConfig(model_name="text-generation/gpt-oss-120b"))
    return {
        "embedding_model": embedding_model_resource,
        "language_model": language_model,
    }
