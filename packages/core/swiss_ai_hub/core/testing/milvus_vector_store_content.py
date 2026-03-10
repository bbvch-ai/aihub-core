import asyncio
from datetime import datetime
from typing import TypeVar

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.schema import TextNode
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from pymilvus import MilvusClient

from swiss_ai_hub.core.generative_ai.resources.models.llm.EmbeddingModelConfig import EmbeddingModelConfig
from swiss_ai_hub.core.infrastructure.milvus.MilvusSettings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
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
from swiss_ai_hub.core.persistence.rag.vectors.stores.MilvusVectorStoreConfig import MilvusVectorStoreConfig

T = TypeVar("T")


def run_with_event_loop(func: callable, *args, **kwargs) -> T:
    """
    Run a synchronous function inside a running event loop.

    LlamaIndex's MilvusVectorStore internally creates an AsyncMilvusClient which requires
    a RUNNING event loop (checked via asyncio.get_running_loop()). This helper creates
    an event loop, runs the function inside it, and returns the result.

    The event loop is kept open after execution because MilvusVectorStore keeps
    references to AsyncMilvusClient which needs the loop.
    """

    async def _wrapper():
        return func(*args, **kwargs)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_wrapper())


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
    def _fill():
        embeddings, _ = embed_model.to_llama_index()
        vs = vector_store.to_llama_index()
        pipeline: IngestionPipeline = IngestionPipeline(
            transformations=[embeddings],
            vector_store=vs,
            docstore=doc_store,
        )
        if nodes:
            pipeline.run(nodes=nodes)
        else:
            pipeline.run(documents=DEFAULT_DOCUMENTS)

    run_with_event_loop(_fill)


def drop_collection(
    uri: str = "http://localhost:19530",
    token: str | None = None,
    collection_name: str = "development",
):
    """Drop a Milvus collection. Uses MilvusSettings token if not explicitly provided."""
    try:
        # Fall back to settings token if not provided
        if token is None:
            token = MilvusSettings().get_token()
        client = MilvusClient(uri=uri, token=token)
        client.drop_collection(collection_name=collection_name)
    except Exception as e:
        print(f"Failed to drop collection: {e}")
