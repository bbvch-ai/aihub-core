from functools import cache
from typing import List

from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore, IndexManagement

from aihub_lib.infrastructure.azure.ai_search.AISearchAccess import AISearchAccess
from aihub_lib.persistence.rag.vectors.node_metadata import (
    DEFAULT_METADATA_FIELDS,
    DOCUMENT_ID,
    NODE_CONTENT,
    NODE_EMBEDDING,
    NODE_ID,
    NODE_METADATA,
)


@cache
def create_azure_ai_search_vector_store(
    vector_store_name: str,
    metadata_fields: List[str] | None = None,
    language: str = "de",
    semantic_configuration_name: str = "mySemanticConfig",
    dimensions: int = 1536,
) -> AzureAISearchVectorStore:
    search_client_singleton = AISearchAccess()
    index_client = search_client_singleton.get_client()

    try:
        index = index_client.get_index(vector_store_name)
        filterable_metadata_field_keys = [field.name for field in index.fields if field.filterable]
    except Exception:
        filterable_metadata_field_keys = metadata_fields or DEFAULT_METADATA_FIELDS

    return AzureAISearchVectorStore(
        search_or_index_client=index_client,
        index_name=vector_store_name,
        filterable_metadata_field_keys=filterable_metadata_field_keys,
        index_management=IndexManagement.CREATE_IF_NOT_EXISTS,
        id_field_key=NODE_ID,
        chunk_field_key=NODE_CONTENT,
        embedding_field_key=NODE_EMBEDDING,
        metadata_string_field_key=NODE_METADATA,
        doc_id_field_key=DOCUMENT_ID,
        language_analyzer=f"{language}.microsoft",
        semantic_configuration_name=semantic_configuration_name,
        embedding_dimensionality=dimensions,
    )
