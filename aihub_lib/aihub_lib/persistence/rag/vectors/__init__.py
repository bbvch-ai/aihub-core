from collections.abc import Callable

from llama_index.core.vector_stores.types import BasePydanticVectorStore

"""Factory function that returns a vector store given a collection name"""
VectorStoreFactory = Callable[[str], BasePydanticVectorStore]
