from typing import Annotated, Literal

from aihub_lib.agents.AgentConfig import StepConfig
from aihub_lib.generative_ai.processors.models.RetrievePrevNextConfig import RetrievePrevNextConfig
from aihub_lib.generative_ai.resources.models.llm.embedding.azure.AzureOpenAIEmbeddingConfig import (
    AzureOpenAIEmbeddingConfig,
)
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
)
from llama_index.core.vector_stores import SimpleVectorStore
from llama_index.core.vector_stores.types import VectorStoreQueryMode
from llama_index.vector_stores.azureaisearch import AzureAISearchVectorStore
from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field, Discriminator, Tag

from aihub_agent.agents.RagAgent.configs.RetrieveSummariesConfig import RetrieveSummariesConfig


def discriminate_vector_store(
    value: dict | SimpleVectorStore | MilvusVectorStore | AzureAISearchVectorStore,
) -> str:
    if isinstance(value, dict):
        return value.get("class_name")
    else:
        return value.class_name()


class RetrieveStepConfig(StepConfig):
    """
    Configuration for the step retrieving documents from a vector store.
    """

    embed_model: Annotated[
        AzureOpenAIEmbeddingConfig | SelfHostedEmbeddingConfig, Field(description="The embedding model configuration.")
    ]
    index_namespaces: Annotated[list[str], Field(description="The namespaces to retrieve from.", min_length=1)]
    retrieve_k: Annotated[int, Field(description="The number of documents to retrieve.", ge=1)]
    query_mode: Annotated[
        VectorStoreQueryMode,
        Field(description="Specifies how the vector store should be queried (e.g., 'default', 'hybrid')."),
    ]
    node_types: Annotated[
        list[Literal["summary", "content"]],
        Field(description="The types of nodes to retrieve (options: 'summary' or 'content').", min_length=1),
    ]
    vector_store: Annotated[
        Annotated[SimpleVectorStore, Tag(SimpleVectorStore.class_name())]
        | Annotated[MilvusVectorStore, Tag(MilvusVectorStore.class_name())]
        | Annotated[AzureAISearchVectorStore, Tag(AzureAISearchVectorStore.class_name())],
        Field(description="The vector store to retrieve from.", discriminator=Discriminator(discriminate_vector_store)),
    ]
    retrieve_prev_next: Annotated[
        RetrievePrevNextConfig | None,
        Field(
            description="Whether to retrieve previous and next nodes "
            "based on the retrieved nodes from the vector store.",
        ),
    ] = None
    retrieve_summaries: Annotated[
        RetrieveSummariesConfig | None,
        Field(
            description="Configurations for retrieving the parent summaries, max number of summary levels",
        ),
    ] = None
