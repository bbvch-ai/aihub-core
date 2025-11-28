import abc
from typing import Annotated

from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import BaseModel, Field


class BasePydanticVectorStoreConfig(BaseModel, abc.ABC):
    dimensions: Annotated[int, Field(description="Dimensions of the embeddings in the vector store")]

    @abc.abstractmethod
    def to_llama_index(self) -> BasePydanticVectorStore:
        pass
