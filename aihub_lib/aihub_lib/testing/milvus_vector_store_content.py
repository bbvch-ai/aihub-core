from datetime import datetime

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import TextNode
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from pymilvus import MilvusClient

from aihub_lib.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from aihub_lib.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    DOCUMENT_TITLE,
    INSERTED_AT,
    NAMESPACE,
    NODE_CONTENT,
    SOURCE,
    TYPE,
    UPDATED_AT,
)
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig

DEFAULT_DOCUMENTS: list[Document] = [
    Document(
        text="AI is crazy. It stands for artificial insanity.",
        metadata={
            DOCUMENT_ID: "Doc1",
            DOCUMENT_TITLE: "Document 1",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_CONTENT,
            CREATED_AT: datetime.now().timestamp(),
            UPDATED_AT: datetime.now().timestamp(),
            INSERTED_AT: datetime.now().timestamp(),
        },
    ),
    Document(
        text="AI is terrible. It stands for artificial ignorance.",
        metadata={
            DOCUMENT_ID: "Doc2",
            DOCUMENT_TITLE: "Document 2",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_CONTENT,
            CREATED_AT: datetime.now().timestamp(),
            UPDATED_AT: datetime.now().timestamp(),
            INSERTED_AT: datetime.now().timestamp(),
        },
    ),
    Document(
        text="AI is amazing. It stands for artificial imagination.",
        metadata={
            DOCUMENT_ID: "Doc3",
            DOCUMENT_TITLE: "Document 3",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_CONTENT,
            CREATED_AT: datetime.now().timestamp(),
            UPDATED_AT: datetime.now().timestamp(),
            INSERTED_AT: datetime.now().timestamp(),
        },
    ),
]


def fill_collection(
    embed_model: EmbeddingModelConfig,
    vector_store: MilvusVectorStoreConfig,
    doc_store: MongoDocumentStore,
    nodes: list[TextNode] | None = None,
):
    embeddings, _ = embed_model.to_llama_index()

    vector_store = vector_store.to_llama_index()

    pipeline: IngestionPipeline = IngestionPipeline(
        transformations=[embeddings],
        vector_store=vector_store,
        docstore=doc_store,
    )
    if nodes:
        pipeline.run(nodes=nodes)
    else:
        pipeline.run(documents=DEFAULT_DOCUMENTS)


def drop_collection(
    uri: str = "http://localhost:19530",
    token: str = "root:Milvus",
    collection_name: str = "development",
):
    try:
        client = MilvusClient(uri=uri, token=token)
        client.drop_collection(collection_name=collection_name)
    except Exception as e:
        print(f"Failed to drop collection: {e}")
