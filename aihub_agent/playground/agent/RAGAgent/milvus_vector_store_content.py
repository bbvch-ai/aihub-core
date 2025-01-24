from typing import List, Optional

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient

from aihub_lib.generative_ai.llms.models.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)

DEFAULT_DOCUMENTS: List[Document] = [
    Document(
        text="AI is crazy. It stands for artificial insanity.",
        metadata={
            "title": "Document 1",
            "author": "Alice",
            "source": "ai_knowledge",
            "namespace": "ai_knowledge",
            "type": "content",
        },
    ),
    Document(
        text="AI is terrible. It stands for artificial ignorance.",
        metadata={
            "title": "Document 2",
            "author": "Bob",
            "source": "ai_knowledge",
            "namespace": "ai_knowledge",
            "type": "content",
        },
    ),
    Document(
        text="AI is amazing. It stands for artificial imagination.",
        metadata={
            "title": "Document 3",
            "author": "Carol",
            "source": "ai_knowledge",
            "namespace": "ai_knowledge",
            "type": "content",
        },
    ),
]


def fill_collection(
    embed_model: SelfHostedEmbeddingConfig,
    vector_store: MilvusVectorStore,
    documents: Optional[List[Document]] = None,
):
    if documents is None:
        documents = DEFAULT_DOCUMENTS

    embeddings, _ = embed_model.to_llama_index(model_parameter=None)
    pipeline: IngestionPipeline = IngestionPipeline(
        transformations=[embeddings],
        vector_store=vector_store,
    )
    for doc in documents:
        pipeline.run(documents=[doc])


def drop_collection(
    uri: str = "http://localhost:19530",
    token: str = "root:Milvus",
    collection_name: str = "development",
):
    client = MilvusClient(uri=uri, token=token)
    client.drop_collection(collection_name=collection_name)
