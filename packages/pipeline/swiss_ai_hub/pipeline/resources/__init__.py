from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
    from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client_resource import S3DataLakeClientResource
    from swiss_ai_hub.pipeline.resources.doc_store.mongo_document_store_resource import MongoDocumentStoreResource
    from swiss_ai_hub.pipeline.resources.llm.embedding_model_resource import EmbeddingModelResource
    from swiss_ai_hub.pipeline.resources.llm.language_model_resource import LanguageModelResource
    from swiss_ai_hub.pipeline.resources.local_file_system.local_file_system_resource import LocalFileSystemResource
    from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource
    from swiss_ai_hub.pipeline.resources.rclone.rclone_resource import RcloneResource
    from swiss_ai_hub.pipeline.resources.share_point.share_point_resource import SharePointResource
    from swiss_ai_hub.pipeline.resources.vector_store.milvus_vector_store_resource import MilvusVectorStoreResource

__all__ = [
    "DocumentParserResource",
    "EmbeddingModelResource",
    "LanguageModelResource",
    "LocalFileSystemResource",
    "MilvusVectorStoreResource",
    "MongoDocumentStoreResource",
    "RcloneResource",
    "S3DataLakeClient",
    "S3DataLakeClientResource",
    "SharePointResource",
]

_LAZY_IMPORTS: dict[str, str] = {
    "DocumentParserResource": "swiss_ai_hub.pipeline.resources.parser.document_parser_resource",
    "EmbeddingModelResource": "swiss_ai_hub.pipeline.resources.llm.embedding_model_resource",
    "LanguageModelResource": "swiss_ai_hub.pipeline.resources.llm.language_model_resource",
    "LocalFileSystemResource": "swiss_ai_hub.pipeline.resources.local_file_system.local_file_system_resource",
    "MilvusVectorStoreResource": "swiss_ai_hub.pipeline.resources.vector_store.milvus_vector_store_resource",
    "MongoDocumentStoreResource": "swiss_ai_hub.pipeline.resources.doc_store.mongo_document_store_resource",
    "RcloneResource": "swiss_ai_hub.pipeline.resources.rclone.rclone_resource",
    "S3DataLakeClient": "swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client",
    "S3DataLakeClientResource": "swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client_resource",
    "SharePointResource": "swiss_ai_hub.pipeline.resources.share_point.share_point_resource",
}


def __getattr__(name: str) -> object:
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        value = getattr(module, name)
        globals()[name] = value
        return value
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
