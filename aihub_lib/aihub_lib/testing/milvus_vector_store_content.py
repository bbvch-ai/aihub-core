from typing import List, Optional

from llama_index.core import Document
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.milvus import MilvusVectorStore
from pymilvus import MilvusClient

from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted import SelfHostedEmbeddingConfig
from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_TITLE, NAMESPACE, NODE_TYPE_CONTENT, SOURCE, TYPE

DEFAULT_DOCUMENTS: List[Document] = [
    Document(
        text="AI is crazy. It stands for artificial insanity.",
        metadata={
            DOCUMENT_TITLE: "Document 1",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_TYPE_CONTENT,
        },
    ),
    Document(
        text="AI is terrible. It stands for artificial ignorance.",
        metadata={
            DOCUMENT_TITLE: "Document 2",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_TYPE_CONTENT,
        },
    ),
    Document(
        text="AI is amazing. It stands for artificial imagination.",
        metadata={
            DOCUMENT_TITLE: "Document 3",
            SOURCE: "ai_knowledge",
            NAMESPACE: "ai_knowledge",
            TYPE: NODE_TYPE_CONTENT,
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
    pipeline.run(documents=documents)


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
