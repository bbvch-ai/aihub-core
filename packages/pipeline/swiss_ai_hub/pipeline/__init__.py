from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from swiss_ai_hub.pipeline.io.doc_store_io_manager import DocStoreIOManager
    from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
    from swiss_ai_hub.pipeline.io.vector_store_io_manager import VectorStoreIOManager
    from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
    from swiss_ai_hub.pipeline.resources.doc_store.mongo_document_store_resource import MongoDocumentStoreResource
    from swiss_ai_hub.pipeline.resources.parser.document_parser_resource import DocumentParserResource
    from swiss_ai_hub.pipeline.resources.vector_store.milvus_vector_store_resource import MilvusVectorStoreResource
    from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
    from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
    from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile, SourceFile
    from swiss_ai_hub.pipeline.util.id_utils import uri_to_id

__all__ = [
    "DataLakeFile",
    "DocStoreIOManager",
    "DocumentParserResource",
    "MilvusVectorStoreResource",
    "MinimalSourceFile",
    "MongoDocumentStoreResource",
    "RefDocDocument",
    "S3DataLakeClient",
    "S3DataLakeIOManager",
    "SourceFile",
    "VectorStoreIOManager",
    "uri_to_id",
]

_LAZY_IMPORTS: dict[str, str] = {
    "DataLakeFile": "swiss_ai_hub.pipeline.types.data_lake_file",
    "DocStoreIOManager": "swiss_ai_hub.pipeline.io.doc_store_io_manager",
    "DocumentParserResource": "swiss_ai_hub.pipeline.resources.parser.document_parser_resource",
    "MilvusVectorStoreResource": "swiss_ai_hub.pipeline.resources.vector_store.milvus_vector_store_resource",
    "MinimalSourceFile": "swiss_ai_hub.pipeline.types.source_file",
    "MongoDocumentStoreResource": "swiss_ai_hub.pipeline.resources.doc_store.mongo_document_store_resource",
    "RefDocDocument": "swiss_ai_hub.pipeline.types.ref_doc_document",
    "S3DataLakeClient": "swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client",
    "S3DataLakeIOManager": "swiss_ai_hub.pipeline.io.s3_data_lake_io_manager",
    "SourceFile": "swiss_ai_hub.pipeline.types.source_file",
    "VectorStoreIOManager": "swiss_ai_hub.pipeline.io.vector_store_io_manager",
    "uri_to_id": "swiss_ai_hub.pipeline.util.id_utils",
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
