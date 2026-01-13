from typing import Annotated

from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import (
    MilvusIndexType,
    create_milvus_vector_store,
)
from dagster import ConfigurableResource, InitResourceContext
from llama_index.vector_stores.milvus import MilvusVectorStore
from pydantic import Field
from pymilvus import MilvusClient


class MilvusVectorStoreResource(ConfigurableResource[MilvusVectorStore]):
    """
    This resource represents a MilvusVectorStore.

    Use this resource either stand-alone whenever you must directly interact with the vector store,
    or use it in conjunction with the ``"vector_store_io_manager"`` resource for a more integrated experience.

    Example usage:

    1. Use the Vector Store as a stand-alone resource

    ... code-block:: python

        from aihub_pipeline.resources.vector_store.MilvusVectorStoreResource import MilvusVectorStoreResource

        from dagster import Definitions, asset

        @asset
        def asset1(vector_store: MilvusVectorStoreResource):
            nodes = vector_store.query(...")


        defs = Definitions(
            assets=[asset1],
            resources={
                "vector_store": MilvusVectorStoreResource(
                    uri="http://localhost",
                    collection_name="my_collection",
                    embedding_vector_dimension=3072,
                ),
            }
        )

    2. Use the Vector store in conjunction with a vector store IO Manager ``"vector_store_io_manager"``

    ... code-block:: python

        from aihub_pipeline.io.VectorStoreIOManager import VectorStoreIOManager
        from aihub_pipeline.resources.vector_store.MilvusVectorStoreResource import MilvusVectorStoreResource

        from dagster import Definitions, asset

        @asset(partitions_def=my_partition, io_manager_key="vector_store_io_manager")
        def text_nodes(ref_doc: RefDocDocument) -> list[TextNode]:
            # TextNodes returned by this asset will be stored in the vector store
            ...

        @asset(partitions_def=my_partition)
        def downstream_asset(text_nodes: list[TextNode]):
            # TextNodes loaded from the vector store
            ...

        vector_store = MilvusVectorStoreResource(
            uri="http://localhost",
            collection_name="my_collection",
            embedding_vector_dimension=1024,
        )
        vector_store_io_manager = VectorStoreIOManager(vector_store=vector_store)

        defs = Definitions(
            assets=[text_nodes, downstream_asset],
            resources={
                "vector_store": vector_store,
                "vector_store_io_manager": vector_store_io_manager,
            }
        )

    """

    uri: str
    collection_name: str
    embedding_vector_dimension: int
    index_type: Annotated[MilvusIndexType, Field(description="Vector index type to use for the embedding field")] = (
        MilvusIndexType.HNSW
    )
    token: Annotated[str | None, Field(description="Authentication token in format 'username:password'")] = None

    def create_resource(self, context: InitResourceContext) -> MilvusVectorStore:
        client = MilvusClient(uri=self.uri, token=self.token)
        return create_milvus_vector_store(
            client=client,
            collection_name=self.collection_name,
            embedding_vector_dimension=self.embedding_vector_dimension,
            index_type=self.index_type,
            uri=self.uri,
            token=self.token,
        )
